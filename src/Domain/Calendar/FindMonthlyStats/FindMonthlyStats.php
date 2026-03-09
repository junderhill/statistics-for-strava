<?php

declare(strict_types=1);

namespace App\Domain\Calendar\FindMonthlyStats;

use App\Infrastructure\CQRS\Query\Query;

/**
 * @implements Query<\App\Domain\Calendar\FindMonthlyStats\FindMonthlyStatsResponse>
 */
final readonly class FindMonthlyStats implements Query
{
    public function __construct(
        private ?int $year = null,
        private ?\App\Domain\Activity\SportType\SportType $sportType = null,
    ) {
    }

    public function getYear(): ?int
    {
        return $this->year;
    }

    public function getSportType(): ?\App\Domain\Activity\SportType\SportType
    {
        return $this->sportType;
    }
}
