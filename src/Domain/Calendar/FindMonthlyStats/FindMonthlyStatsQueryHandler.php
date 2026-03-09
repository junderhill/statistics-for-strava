<?php

declare(strict_types=1);

namespace App\Domain\Calendar\FindMonthlyStats;

use App\Domain\Activity\ActivityType;
use App\Domain\Activity\ActivityTypes;
use App\Domain\Activity\SportType\SportType;
use App\Domain\Calendar\Month;
use App\Infrastructure\CQRS\Query\Query;
use App\Infrastructure\CQRS\Query\QueryHandler;
use App\Infrastructure\CQRS\Query\Response;
use App\Infrastructure\ValueObject\Measurement\Length\Meter;
use App\Infrastructure\ValueObject\Measurement\Time\Seconds;
use App\Infrastructure\ValueObject\Time\SerializableDateTime;
use Doctrine\DBAL\ArrayParameterType;
use Doctrine\DBAL\Connection;

final readonly class FindMonthlyStatsQueryHandler implements QueryHandler
{
    public function __construct(
        private Connection $connection,
    ) {
    }

    public function handle(Query $query): Response
    {
        assert($query instanceof FindMonthlyStats);

        $sql = <<<SQL
            SELECT strftime('%Y-%m', startDateTime) AS yearAndMonth,
                   sportType,
                   COUNT(*) AS numberOfActivities,
                   SUM(distance) AS totalDistance,
                   SUM(elevation) AS totalElevation,
                   SUM(movingTimeInSeconds) AS totalMovingTime,
                   SUM(calories) as totalCalories
            FROM Activity
            WHERE 1=1
        SQL;

        $params = [];

        if ($query->getYear() !== null) {
            $sql .= ' AND strftime(\'%Y\', startDateTime) = :year';
            $params['year'] = (string) $query->getYear();
        }

        if ($query->getSportType() !== null) {
            $sql .= ' AND sportType = :sportType';
            $params['sportType'] = $query->getSportType()->value;
        }

        $sql .= ' GROUP BY yearAndMonth, sportType';

        $results = $this->connection->executeQuery($sql, $params)->fetchAllAssociative();

        $statsPerMonth = [];
        $activityTypes = ActivityTypes::empty();
        foreach ($results as $result) {
            $month = Month::fromDate(SerializableDateTime::fromString(sprintf('%s-01 00:00:00', $result['yearAndMonth'])));
            $sportType = SportType::from($result['sportType']);

            if (!$activityTypes->has($sportType->getActivityType())) {
                $activityTypes->add($sportType->getActivityType());
            }

            $statsPerMonth[] = [
                'month' => $month,
                'sportType' => $sportType,
                'numberOfActivities' => (int) $result['numberOfActivities'],
                'distance' => Meter::from($result['totalDistance'])->toKilometer(),
                'elevation' => Meter::from($result['totalElevation']),
                'movingTime' => Seconds::from($result['totalMovingTime']),
                'calories' => (int) $result['totalCalories'],
            ];
        }

        $minMaxDatePerActivityType = [];
        /** @var ActivityType $activityType */
        foreach ($activityTypes as $activityType) {
            $sql = <<<SQL
                SELECT MIN(startDateTime) AS minStartDate,
                       MAX(startDateTime) AS maxStartDate
                FROM Activity
                WHERE sportType IN (:sportTypes)
            SQL;

            $params = [
                'sportTypes' => $activityType->getSportTypes()->map(fn (SportType $sportType) => $sportType->value),
            ];
            $paramTypes = [
                'sportTypes' => ArrayParameterType::STRING,
            ];

            if ($query->getYear() !== null) {
                $sql .= ' AND strftime(\'%Y\', startDateTime) = :year';
                $params['year'] = (string) $query->getYear();
                $paramTypes['year'] = \PDO::PARAM_STR;
            }

            if ($query->getSportType() !== null) {
                $sql .= ' AND sportType = :sportType';
                $params['sportType'] = $query->getSportType()->value;
                $paramTypes['sportType'] = \PDO::PARAM_STR;
            }

            /** @var non-empty-array<string, string> $result */
            $result = $this->connection->executeQuery($sql, $params, $paramTypes)->fetchAssociative();

            $minMaxDatePerActivityType[] = [
                'activityType' => $activityType,
                'min' => Month::fromDate(SerializableDateTime::fromString($result['minStartDate'])),
                'max' => Month::fromDate(SerializableDateTime::fromString($result['maxStartDate'])),
            ];
        }

        return new FindMonthlyStatsResponse(
            statsPerMonth: $statsPerMonth,
            minMaxMonthPerActivityType: $minMaxDatePerActivityType,
        );
    }
}
