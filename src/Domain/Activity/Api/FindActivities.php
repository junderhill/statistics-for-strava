<?php

declare(strict_types=1);

namespace App\Domain\Activity\Api;

use App\Infrastructure\CQRS\Query\Query;

/**
 * @implements Query<\App\Infrastructure\Http\Api\ActivitiesResponse>
 */
final readonly class FindActivities implements Query
{
    public function __construct(
        private ?\DateTimeImmutable $since = null,
        private ?\App\Domain\Activity\SportType\SportType $sportType = null,
        private int $page = 1,
        private int $limit = 50,
    ) {
    }

    public function getSince(): ?\DateTimeImmutable
    {
        return $this->since;
    }

    public function getSportType(): ?\App\Domain\Activity\SportType\SportType
    {
        return $this->sportType;
    }

    public function getPage(): int
    {
        return $this->page;
    }

    public function getLimit(): int
    {
        return $this->limit;
    }
}