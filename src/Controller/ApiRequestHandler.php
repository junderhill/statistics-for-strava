<?php

declare(strict_types=1);

namespace App\Controller;

use App\Domain\Activity\Api\FindActivities;
use App\Domain\Activity\SportType\SportType;
use App\Domain\Calendar\FindMonthlyStats\FindMonthlyStats;
use App\Infrastructure\CQRS\Query\Bus\QueryBus;
use App\Infrastructure\Http\Api\ActivitiesResponse;
use App\Infrastructure\Http\Api\MonthlyStatsResponse;
use App\Infrastructure\Serialization\Json;
use App\Infrastructure\ValueObject\String\CompressedString;
use League\Flysystem\FilesystemOperator;
use League\Flysystem\UnableToReadFile;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Attribute\AsController;
use Symfony\Component\Routing\Attribute\Route;

#[AsController]
final readonly class ApiRequestHandler
{
    public function __construct(
        private FilesystemOperator $apiStorage,
        private QueryBus $queryBus,
    ) {
    }

    #[Route(path: '/api/{path}', requirements: ['path' => '[a-zA-Z0-9_\-/.]+'], methods: ['GET'], priority: 2)]
    public function handle(string $path, Request $request): Response
    {
        // Handle dynamic API routes
        if ($path === 'activities') {
            return $this->handleActivitiesRequest($request);
        }

        if ($path === 'stats/monthly') {
            return $this->handleMonthlyStatsRequest($request);
        }

        // Fall back to static file serving for legacy/static API files
        try {
            if (!$this->apiStorage->fileExists($path)) {
                return new Response('', Response::HTTP_NOT_FOUND);
            }

            $fileContents = $this->apiStorage->read($path);

            if (str_ends_with($path, '.gpx')) {
                $response = new Response(CompressedString::fromCompressed($fileContents)->uncompress());
                $response->headers->set('Content-Type', 'application/gpx+xml; charset=UTF-8');

                return $response;
            }

            return new JsonResponse(
                data: Json::uncompressAndDecode($fileContents),
                status: Response::HTTP_OK
            );
        } catch (UnableToReadFile) {
            return new Response('', Response::HTTP_NOT_FOUND);
        }
    }

    private function handleActivitiesRequest(Request $request): Response
    {
        // Parse query parameters
        $since = $request->query->get('since');
        $sportTypeParam = $request->query->get('sportType');
        $page = (int) $request->query->get('page', 1);
        $limit = (int) $request->query->get('limit', 50);

        // Validate and parse parameters
        $sinceDate = null;
        if ($since !== null) {
            try {
                $sinceDate = new \DateTimeImmutable($since);
            } catch (\Exception $e) {
                return new JsonResponse(
                    ['error' => 'Invalid since parameter. Expected valid date format.'],
                    Response::HTTP_BAD_REQUEST
                );
            }
        }

        $sportType = null;
        if ($sportTypeParam !== null) {
            try {
                $sportType = SportType::from($sportTypeParam);
            } catch (\Exception $e) {
                return new JsonResponse(
                    ['error' => 'Invalid sportType parameter.'],
                    Response::HTTP_BAD_REQUEST
                );
            }
        }

        // Validate pagination parameters
        if ($page < 1) {
            $page = 1;
        }
        if ($limit < 1 || $limit > 100) {
            $limit = 50;
        }

        // Execute query
        $query = new FindActivities($sinceDate, $sportType, $page, $limit);
        $response = $this->queryBus->ask($query);

        assert($response instanceof ActivitiesResponse);

        return new JsonResponse(
            data: $response->toArray(),
            status: Response::HTTP_OK
        );
    }

    private function handleMonthlyStatsRequest(Request $request): Response
    {
        // Parse query parameters
        $year = $request->query->get('year');
        $sportTypeParam = $request->query->get('sportType');

        $yearInt = null;
        if ($year !== null) {
            if (!ctype_digit($year) || (int)$year < 2000 || (int)$year > 2100) {
                return new JsonResponse(
                    ['error' => 'Invalid year parameter. Expected 4-digit year between 2000-2100.'],
                    Response::HTTP_BAD_REQUEST
                );
            }
            $yearInt = (int) $year;
        }

        $sportType = null;
        if ($sportTypeParam !== null) {
            try {
                $sportType = SportType::from($sportTypeParam);
            } catch (\Exception $e) {
                return new JsonResponse(
                    ['error' => 'Invalid sportType parameter.'],
                    Response::HTTP_BAD_REQUEST
                );
            }
        }

        // Execute query
        $query = new FindMonthlyStats($yearInt, $sportType);
        $monthlyStats = $this->queryBus->ask($query);

        assert($monthlyStats instanceof \App\Domain\Calendar\FindMonthlyStats\FindMonthlyStatsResponse);

        $response = new MonthlyStatsResponse($monthlyStats);

        return new JsonResponse(
            data: $response->toArray(),
            status: Response::HTTP_OK
        );
    }
}
