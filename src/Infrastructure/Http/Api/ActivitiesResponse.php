<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Api;

use App\Infrastructure\CQRS\Query\Response;

final readonly class ActivitiesResponse implements Response
{
    public function __construct(
        private \App\Domain\Activity\Activities $activities,
        private int $totalCount,
        private int $page,
        private int $limit,
        private int $totalPages,
    ) {
    }

    public function toArray(): array
    {
        return [
            'data' => array_map(
                fn (\App\Domain\Activity\Activity $activity) => [
                    'id' => $activity->getId()->toString(),
                    'name' => $activity->getOriginalName(),
                    'sportType' => $activity->getSportType()->value,
                    'activityType' => $activity->getSportType()->getActivityType()->value,
                    'distance' => $activity->getDistance()->toFloat(),
                    'movingTime' => $activity->getMovingTimeInSeconds(),
                    'totalElevationGain' => $activity->getElevation()->toInt(),
                    'averageSpeed' => $activity->getAverageSpeed()->toFloat(),
                    'maxSpeed' => $activity->getMaxSpeed()->toFloat(),
                    'averageHeartRate' => $activity->getAverageHeartRate(),
                    'maxHeartRate' => $activity->getMaxHeartRate(),
                    'averagePower' => $activity->getAveragePower(),
                    'maxPower' => $activity->getMaxPower(),
                    'startDate' => $activity->getStartDate()->format('Y-m-d\TH:i:s\Z'),
                    'kudosCount' => $activity->getKudoCount(),
                    'isCommute' => $activity->isCommute(),
                    'deviceName' => $activity->getDeviceName(),
                ],
                $this->activities->toArray()
            ),
            'pagination' => [
                'total' => $this->totalCount,
                'page' => $this->page,
                'limit' => $this->limit,
                'totalPages' => $this->totalPages,
                'hasNextPage' => $this->page < $this->totalPages,
                'hasPreviousPage' => $this->page > 1,
            ],
        ];
    }
}