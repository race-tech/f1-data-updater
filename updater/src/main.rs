use std::env;

use chrono::Datelike;
use mysql::{prelude::*, Transaction};
use sea_query::{MysqlQueryBuilder, Query};

mod models;
mod tables;

use simple_logger::SimpleLogger;
use tables::*;

fn main() -> anyhow::Result<()> {
    SimpleLogger::new().init()?;

    log::info!("starting with args: {:?}", env::args());
    let round = env::args().nth(1).unwrap().parse::<u16>()?;
    let is_sprint = env::args().nth(2).unwrap().parse::<bool>()?;
    let year = chrono::Utc::now().year();

    let url = "mysql://root:password@localhost:13306/f1db";
    let pool = mysql::Pool::new(url)?;
    let mut conn = pool.get_conn()?;

    let race_id = *conn
        .query_map(
            format!("SELECT raceId FROM races WHERE round = {round} AND year = {year}"),
            |race_id: i32| race_id,
        )?
        .first()
        .expect("race not found");

    let mut tx = conn.start_transaction(mysql::TxOpts::default())?;

    lap_times(race_id, &mut tx)?;
    pit_stops(race_id, &mut tx)?;
    qualifying_results(race_id, &mut tx)?;
    driver_results(race_id, &mut tx)?;
    driver_championship(race_id, &mut tx)?;
    constructor_championship(race_id, &mut tx)?;

    if !is_sprint {
        constructor_results(race_id, &mut tx)?;
    } else {
        constructor_sprint_results(race_id, &mut tx)?;
        sprint_lap_times(race_id, &mut tx)?;
        driver_sprint_results(race_id, &mut tx)?;
    }

    tx.commit()?;
    log::info!("transaction committed");

    Ok(())
}

fn lap_times(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/laps_analysis.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    for r in rdr.deserialize::<models::LapAnalysis>() {
        let la = r?;
        log::info!("inserting lap analysis: {:?}", la);

        let driver_id = *tx
            .query_map(
                format!("SELECT driverId FROM drivers WHERE code = {}", la.driver),
                |driver_id: i32| driver_id,
            )?
            .first()
            .expect("driver not found");

        let q = Query::insert()
            .into_table(LapTimes::Table)
            .columns([
                LapTimes::RaceID,
                LapTimes::DriverID,
                LapTimes::Lap,
                LapTimes::Position,
                LapTimes::Time,
                LapTimes::Milliseconds,
            ])
            .values([
                race_id.into(),
                driver_id.into(),
                la.lap.into(),
                la.position.into(),
                la.time.into(),
                la.milliseconds.into(),
            ])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("lap_times inserted");
    Ok(())
}

fn pit_stops(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/pit_stops.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    for r in rdr.deserialize::<models::PitStop>() {
        let ps = r?;
        log::info!("inserting pit stop: {:?}", ps);

        let driver_id = *tx
            .query_map(
                format!("SELECT driverId FROM drivers WHERE code = {}", ps.no),
                |driver_id: i32| driver_id,
            )?
            .first()
            .expect("driver not found");

        let q = Query::insert()
            .into_table(PitStops::Table)
            .columns([
                PitStops::RaceID,
                PitStops::DriverID,
                PitStops::Stop,
                PitStops::Lap,
                PitStops::Time,
                PitStops::Duration,
                PitStops::Milliseconds,
            ])
            .values([
                race_id.into(),
                driver_id.into(),
                ps.stop.into(),
                ps.lap.into(),
                ps.time.into(),
                ps.duration.into(),
                ps.milliseconds.into(),
            ])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("pit_stops inserted");
    Ok(())
}

fn qualifying_results(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/quali_classification.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    for r in rdr.deserialize::<models::QualificationOrder>() {
        let qo = r?;
        log::info!("qualification order: {:?}", qo);

        let driver_id = *tx
            .query_map(
                format!("SELECT driverId FROM drivers WHERE code = {}", qo.no),
                |driver_id: i32| driver_id,
            )?
            .first()
            .expect("driver not found");
        let constructor_id = *tx
            .query_map(
                format!(
                    "SELECT constructorId FROM constructors WHERE name = {}",
                    qo.entrant
                ),
                |constructor_id: i32| constructor_id,
            )?
            .first()
            .expect("constructor not found");

        // TODO: Handle status

        let q = Query::insert()
            .into_table(Qualifying::Table)
            .columns([
                Qualifying::RaceID,
                Qualifying::DriverID,
                Qualifying::ConstructorID,
                Qualifying::Number,
                Qualifying::Position,
                Qualifying::Q1,
                Qualifying::Q2,
                Qualifying::Q3,
            ])
            .values([
                race_id.into(),
                driver_id.into(),
                constructor_id.into(),
                qo.no.into(),
                qo.pos.into(),
                qo.q1_time.into(),
                qo.q2_time.into(),
                qo.q3_time.into(),
            ])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("qualifying_results inserted");
    Ok(())
}

fn driver_results(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/driver_race_result.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    for r in rdr.deserialize::<models::DriverRaceResult>() {
        let drr = r?;
        log::info!("inserting driver race result: {:?}", drr);

        let driver_id = *tx
            .query_map(
                format!("SELECT driverId FROM drivers WHERE code = {}", drr.no),
                |driver_id: i32| driver_id,
            )?
            .first()
            .expect("driver not found");
        let constructor_id = *tx
            .query_map(
                format!(
                    "SELECT constructorId FROM constructors WHERE name = {}",
                    drr.entrant
                ),
                |constructor_id: i32| constructor_id,
            )?
            .first()
            .expect("constructor not found");

        // TODO: Handle status

        let q = Query::insert()
            .into_table(Results::Table)
            .columns([
                Results::RaceID,
                Results::DriverID,
                Results::ConstructorID,
                Results::Number,
                Results::Grid,
                Results::Position,
                Results::PositionText,
                Results::PositionOrder,
                Results::Points,
                Results::Laps,
                Results::Time,
                Results::Milliseconds,
                Results::FastestLap,
                Results::Rank,
                Results::FastestLapTime,
                Results::FastestLapSpeed,
            ])
            .values([
                race_id.into(),
                driver_id.into(),
                constructor_id.into(),
                drr.no.into(),
                drr.grid.into(),
                drr.position.into(),
                drr.position.into(),
                drr.position_order.into(),
                drr.points.into(),
                drr.laps.into(),
                drr.time.into(),
                drr.milliseconds.into(),
                drr.fastest_lap.into(),
                drr.rank.into(),
                drr.fatest_lap_time.into(),
                drr.fastest_lap_speed.into(),
            ])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("driver race results inserted");
    Ok(())
}

fn constructor_results(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/constructor_race_result.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    for r in rdr.deserialize::<models::ConstructorRaceResult>() {
        let crr = r?;
        log::info!("inserting constructor result: {:?}", crr);

        let constructor_id = *tx
            .query_map(
                format!(
                    "SELECT constructorId FROM constructors WHERE name = {}",
                    crr.constructor
                ),
                |constructor_id: i32| constructor_id,
            )?
            .first()
            .expect("constructor not found");

        let q = Query::insert()
            .into_table(ConstructorResults::Table)
            .columns([
                ConstructorResults::RaceID,
                ConstructorResults::ConstructorID,
                ConstructorResults::Points,
            ])
            .values([race_id.into(), constructor_id.into(), crr.points.into()])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("constructor race results inserted");
    Ok(())
}

fn driver_championship(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/drivers_championship.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    for r in rdr.deserialize::<models::DriverChampionship>() {
        let dd = r?;
        log::info!("inserting driver championship: {:?}", dd);

        let surname = dd
            .driver
            .split_once(' ')
            .expect("no driver surname")
            .1
            .to_ascii_lowercase();

        let driver_id = *tx
            .query_map(
                format!("SELECT driverId FROM drivers WHERE surname = {}", surname),
                |driver_id: i32| driver_id,
            )?
            .first()
            .expect("driver not found");

        let q = Query::insert()
            .into_table(DriverStandings::Table)
            .columns([
                DriverStandings::RaceID,
                DriverStandings::DriverID,
                DriverStandings::Points,
                DriverStandings::Position,
                DriverStandings::PositionText,
                DriverStandings::Wins,
            ])
            .values([
                race_id.into(),
                driver_id.into(),
                dd.points.into(),
                dd.position.into(),
                dd.position.into(),
                dd.wins.into(),
            ])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("driver championship inserted");
    Ok(())
}

fn constructor_championship(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/constructors_championship.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    for r in rdr.deserialize::<models::ConstructorChampionship>() {
        let cc = r?;
        log::info!("inserting constructor championship: {:?}", cc);

        let constructor_id = *tx
            .query_map(
                format!(
                    "SELECT constructorId FROM constructors WHERE name = {}",
                    cc.constructor
                ),
                |constructor_id: i32| constructor_id,
            )?
            .first()
            .expect("constructor not found");

        let q = Query::insert()
            .into_table(ConstructorStandings::Table)
            .columns([
                ConstructorStandings::RaceID,
                ConstructorStandings::ConstructorID,
                ConstructorStandings::Points,
                ConstructorStandings::Position,
                ConstructorStandings::PositionText,
                ConstructorStandings::Wins,
            ])
            .values([
                race_id.into(),
                constructor_id.into(),
                cc.points.into(),
                cc.position.into(),
                cc.position.into(),
                cc.wins.into(),
            ])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("constructor championship inserted");
    Ok(())
}

fn sprint_lap_times(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/sprint_laps_analysis.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    for r in rdr.deserialize::<models::LapAnalysis>() {
        let la = r?;
        log::info!("inserting sprint lap time: {:?}", la);

        let driver_id = *tx
            .query_map(
                format!("SELECT driverId FROM drivers WHERE code = {}", la.driver),
                |driver_id: i32| driver_id,
            )?
            .first()
            .expect("driver not found");

        let q = Query::insert()
            .into_table(LapTimes::Table)
            .columns([
                LapTimes::RaceID,
                LapTimes::DriverID,
                LapTimes::Lap,
                LapTimes::Position,
                LapTimes::Time,
                LapTimes::Milliseconds,
            ])
            .values([
                race_id.into(),
                driver_id.into(),
                la.lap.into(),
                la.position.into(),
                la.time.into(),
                la.milliseconds.into(),
            ])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("sprint lap times inserted");
    Ok(())
}

fn driver_sprint_results(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/driver_sprint_result.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    for r in rdr.deserialize::<models::DriverSprintResult>() {
        let dsr = r?;
        log::info!("inserting driver sprint result: {:?}", dsr);

        let driver_id = *tx
            .query_map(
                format!("SELECT driverId FROM drivers WHERE code = {}", dsr.no),
                |driver_id: i32| driver_id,
            )?
            .first()
            .expect("driver not found");
        let constructor_id = *tx
            .query_map(
                format!(
                    "SELECT constructorId FROM constructors WHERE name = {}",
                    dsr.entrant
                ),
                |constructor_id: i32| constructor_id,
            )?
            .first()
            .expect("constructor not found");

        // TODO: Handle status

        let q = Query::insert()
            .into_table(SprintResults::Table)
            .columns([
                SprintResults::RaceID,
                SprintResults::DriverID,
                SprintResults::ConstructorID,
                SprintResults::Number,
                SprintResults::Grid,
                SprintResults::Position,
                SprintResults::PositionText,
                SprintResults::PositionOrder,
                SprintResults::Points,
                SprintResults::Laps,
                SprintResults::Time,
                SprintResults::Milliseconds,
                SprintResults::FastestLap,
                SprintResults::FastestLapTime,
                SprintResults::FastestLapSpeed,
            ])
            .values([
                race_id.into(),
                driver_id.into(),
                constructor_id.into(),
                dsr.no.into(),
                dsr.grid.into(),
                dsr.position.into(),
                dsr.position.into(),
                dsr.position_order.into(),
                dsr.points.into(),
                dsr.laps.into(),
                dsr.time.into(),
                dsr.milliseconds.into(),
                dsr.fastest_lap.into(),
                dsr.fatest_lap_time.into(),
                dsr.fastest_lap_speed.into(),
            ])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("driver sprint results inserted");
    Ok(())
}

fn constructor_sprint_results(race_id: i32, tx: &mut Transaction) -> anyhow::Result<()> {
    let file = "/etc/csv/constructor_race_result.csv";
    let mut rdr = csv::Reader::from_path(file)?;

    let driver_sprint_file = "/etc/csv/driver_sprint_result.csv";
    let mut driver_sprint_rdr = csv::Reader::from_path(driver_sprint_file)?;

    let drivers = driver_sprint_rdr
        .deserialize::<models::DriverSprintResult>()
        .collect::<Result<Vec<_>, _>>()?;

    for r in rdr.deserialize::<models::ConstructorRaceResult>() {
        let crr = r?;
        log::info!("inserting constructor sprint result: {:?}", crr);

        let sprint_points = drivers
            .iter()
            .filter(|d| d.entrant == crr.constructor)
            .map(|d| d.points)
            .sum::<u16>()
            + crr.points;

        let constructor_id = *tx
            .query_map(
                format!(
                    "SELECT constructorId FROM constructors WHERE name = {}",
                    crr.constructor
                ),
                |constructor_id: i32| constructor_id,
            )?
            .first()
            .expect("constructor not found");

        let q = Query::insert()
            .into_table(ConstructorResults::Table)
            .columns([
                ConstructorResults::RaceID,
                ConstructorResults::ConstructorID,
                ConstructorResults::Points,
            ])
            .values([race_id.into(), constructor_id.into(), sprint_points.into()])?
            .to_string(MysqlQueryBuilder);

        tx.exec_drop(q, ())?;
    }

    log::info!("constructor sprint result inserted");
    Ok(())
}
