<?php

declare(strict_types=1);

namespace App\Domain\Activity\Api;

use App\Infrastructure\CQRS\Query\Query;
use App\Infrastructure\CQRS\Query\QueryHandler;
use App\Infrastructure\Http\Api\ActivitiesResponse;

final readonly class FindActivitiesQueryHandler implements QueryHandler
{
    public function __construct(
        private \App\Domain\Activity\ActivityRepository $activityRepository,
    ) {
    }

    public function handle(Query $query): \App\Infrastructure\CQRS\Query\Response
    {
        assert($query instanceof FindActivities);

        $results = $this->activityRepository->findAllWithFilters(
            $query->getSince(),
            $query->getSportType(),
            $query->getPage(),
            $query->getLimit(),
        );

        return new ActivitiesResponse(
            activities: $results['activities'],
            totalCount: $results['totalCount'],
            page: $results['page'],
            limit: $results['limit'],
            totalPages: $results['totalPages'],
        );
    }
}