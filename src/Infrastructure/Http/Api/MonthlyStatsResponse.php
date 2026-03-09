<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Api;

use App\Infrastructure\CQRS\Query\Response;

final readonly class MonthlyStatsResponse implements Response
{
    public function __construct(
        private \App\Domain\Calendar\FindMonthlyStats\FindMonthlyStatsResponse $monthlyStats,
    ) {
    }

    public function toArray(): array
    {
        $totals = $this->monthlyStats->getTotals();

        $monthlyBreakdown = [];

        // Group stats by month
        $statsByMonth = [];
        foreach ($this->monthlyStats->getStatsPerMonth() as $stats) {
            $monthId = $stats['month']->getId();
            if (!isset($statsByMonth[$monthId])) {
                $statsByMonth[$monthId] = [
                    'month' => $stats['month']->getId(),
                    'monthsAgo' => $this->calculateMonthsAgo($stats['month']),
                    'sportTypes' => [],
                    'totals' => [
                        'numberOfActivities' => 0,
                        'distance' => 0.0,
                        'elevation' => 0,
                        'movingTime' => 0,
                        'calories' => 0,
                    ],
                ];
            }

            $statsByMonth[$monthId]['sportTypes'][] = [
                'sportType' => $stats['sportType']->value,
                'numberOfActivities' => $stats['numberOfActivities'],
                'distance' => $stats['distance']->toFloat(),
                'elevation' => $stats['elevation']->toInt(),
                'movingTime' => $stats['movingTime']->toInt(),
                'calories' => $stats['calories'],
            ];

            // Update monthly totals
            $statsByMonth[$monthId]['totals']['numberOfActivities'] += $stats['numberOfActivities'];
            $statsByMonth[$monthId]['totals']['distance'] += $stats['distance']->toFloat();
            $statsByMonth[$monthId]['totals']['elevation'] += $stats['elevation']->toInt();
            $statsByMonth[$monthId]['totals']['movingTime'] += $stats['movingTime']->toInt();
            $statsByMonth[$monthId]['totals']['calories'] += $stats['calories'];
        }

        // Sort by month (newest first)
        krsort($statsByMonth);

        return [
            'data' => array_values($statsByMonth),
            'summary' => [
                'numberOfActivities' => $totals['numberOfActivities'],
                'distance' => $totals['distance']->toFloat(),
                'elevation' => $totals['elevation']->toInt(),
                'movingTime' => $totals['movingTime']->toInt(),
                'calories' => $totals['calories'],
            ],
        ];
    }

    private function calculateMonthsAgo(\App\Domain\Calendar\Month $month): int
    {
        $now = new \DateTimeImmutable();
        $currentMonth = \App\Domain\Calendar\Month::fromDate($now);

        $currentYear = $currentMonth->getYear();
        $currentMonthNum = $currentMonth->getMonth();
        $targetYear = $month->getYear();
        $targetMonthNum = $month->getMonth();

        return ($currentYear - $targetYear) * 12 + ($currentMonthNum - $targetMonthNum);
    }
}