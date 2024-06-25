use std::{env, process::exit};

use chrono::Datelike;
use mysql::{prelude::*, PooledConn};

mod models;
mod tables;

fn main() -> anyhow::Result<()> {
    let url = "mysql://root:password@localhost:13306/f1db";
    let pool = mysql::Pool::new(url)?;
    let mut conn = pool.get_conn()?;

    let round = env::args().nth(1).unwrap().parse::<u16>()?;
    let year = chrono::Utc::now().year();

    let race_id = *conn
        .query_map(
            format!("SELECT raceId FROM races WHERE round = {round} AND year = {year}"),
            |race_id: i32| race_id,
        )?
        .first()
        .expect("race not found");

    check(race_id, &mut conn)?;

    Ok(())
}

fn check(race_id: i32, conn: &mut PooledConn) -> anyhow::Result<()> {
    let results: Vec<i32> = conn.query(format!(
        "SELECT resultId FROM results WHERE raceId = {race_id}"
    ))?;

    if !results.is_empty() {
        println!("table already have been updated");
        exit(0);
    }

    Ok(())
}
