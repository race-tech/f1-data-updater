use sea_query::Iden;

#[derive(Iden)]
pub enum ConstructorResults {
    Table,
    #[iden = "raceId"]
    RaceID,
    #[iden = "constructorId"]
    ConstructorID,
    Points,
    Status,
}

#[derive(Iden)]
pub enum ConstructorStandings {
    Table,
    #[iden = "raceId"]
    RaceID,
    #[iden = "constructorId"]
    ConstructorID,
    Points,
    Position,
    #[iden = "positionText"]
    PositionText,
    Wins,
}

#[derive(Iden)]
pub enum DriverStandings {
    Table,
    #[iden = "raceId"]
    RaceID,
    #[iden = "driverId"]
    DriverID,
    Points,
    Position,
    #[iden = "positionText"]
    PositionText,
    Wins,
}

#[derive(Iden)]
pub enum LapTimes {
    Table,
    #[iden = "raceId"]
    RaceID,
    #[iden = "driverId"]
    DriverID,
    Lap,
    Position,
    Time,
    Milliseconds,
}

#[derive(Iden)]
pub enum PitStops {
    Table,
    #[iden = "raceId"]
    RaceID,
    #[iden = "driverId"]
    DriverID,
    Stop,
    Lap,
    Time,
    Duration,
    Milliseconds,
}

#[derive(Iden)]
pub enum Qualifying {
    Table,
    #[iden = "raceId"]
    RaceID,
    #[iden = "driverId"]
    DriverID,
    #[iden = "constructorId"]
    ConstructorID,
    Number,
    Position,
    Q1,
    Q2,
    Q3,
}

#[derive(Iden)]
pub enum Results {
    Table,
    #[iden = "raceId"]
    RaceID,
    #[iden = "driverId"]
    DriverID,
    #[iden = "constructorId"]
    ConstructorID,
    Number,
    Grid,
    Position,
    #[iden = "positionText"]
    PositionText,
    #[iden = "positionOrder"]
    PositionOrder,
    Points,
    Laps,
    Time,
    Milliseconds,
    #[iden = "fastestLap"]
    FastestLap,
    Rank,
    #[iden = "fastestLapTime"]
    FastestLapTime,
    #[iden = "fastestLapSpeed"]
    FastestLapSpeed,
    #[iden = "statusId"]
    StatusID,
}

#[derive(Iden)]
pub enum SprintResults {
    Table,
    #[iden = "raceId"]
    RaceID,
    #[iden = "driverId"]
    DriverID,
    #[iden = "constructorId"]
    ConstructorID,
    Number,
    Grid,
    Position,
    #[iden = "positionText"]
    PositionText,
    #[iden = "positionOrder"]
    PositionOrder,
    Points,
    Laps,
    Time,
    Milliseconds,
    #[iden = "fastestLap"]
    FastestLap,
    #[iden = "fastestLapTime"]
    FastestLapTime,
    #[iden = "fastestLapSpeed"]
    FastestLapSpeed,
    #[iden = "statusId"]
    StatusID,
}
