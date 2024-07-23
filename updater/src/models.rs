use serde::de::Error;
use serde::{Deserialize, Deserializer};

#[derive(Deserialize, Debug)]
pub struct LapAnalysis {
    pub position: u16,
    pub driver_no: u16,
    pub gap: String,
    #[serde(deserialize_with = "de_time")]
    pub duration: chrono::TimeDelta,
    pub time: String,
    pub lap: u16,
}

#[derive(Deserialize, Debug)]
pub struct QualificationOrder {
    pub pos: u16,
    pub no: u16,
    pub driver: String,
    pub entrant: String,
    pub q1: String,
    pub q1_laps: u32,
    pub q1_time: String,
    pub q2: Option<String>,
    pub q2_laps: Option<u32>,
    pub q2_time: Option<String>,
    pub q3: Option<String>,
    pub q3_laps: Option<u32>,
    pub q3_time: Option<String>,
}

#[derive(Deserialize, Debug)]
pub struct DriverRaceResult {
    pub no: u16,
    pub entrant: String,
    pub grid: u16,
    pub position: String,
    #[serde(rename = "positionOrder")]
    pub position_order: u16,
    pub points: u16,
    pub laps: u16,
    pub time: Option<String>,
    pub milliseconds: Option<String>,
    #[serde(rename = "fastestLap")]
    pub fastest_lap: Option<u16>,
    pub rank: Option<u16>,
    #[serde(rename = "fastestLapTime")]
    pub fatest_lap_time: Option<String>,
    #[serde(rename = "fastestLapSpeed")]
    pub fastest_lap_speed: Option<f32>,
}

#[derive(Deserialize, Debug)]
pub struct DriverSprintResult {
    pub no: u16,
    pub entrant: String,
    pub grid: u16,
    pub position: String,
    #[serde(rename = "positionOrder")]
    pub position_order: u16,
    pub points: u16,
    pub laps: u16,
    pub time: Option<String>,
    pub milliseconds: Option<String>,
    #[serde(rename = "fastestLap")]
    pub fastest_lap: Option<u16>,
    #[serde(rename = "fastestLapTime")]
    pub fatest_lap_time: Option<String>,
    #[serde(rename = "fastestLapSpeed")]
    pub fastest_lap_speed: Option<f32>,
}

#[derive(Deserialize, Debug)]
pub struct ConstructorRaceResult {
    pub constructor: String,
    pub points: u16,
}

#[derive(Deserialize, Debug)]
pub struct DriverChampionship {
    pub driver: String,
    pub points: u32,
    pub position: u32,
    pub wins: u32,
}

#[derive(Deserialize, Debug)]
pub struct ConstructorChampionship {
    pub constructor: String,
    pub points: u32,
    pub position: u32,
    pub wins: u32,
}

#[derive(Deserialize, Debug)]
pub struct PitStop {
    pub no: u16,
    pub driver: String,
    pub stop: u32,
    pub lap: u16,
    pub time: String,
    pub duration: String,
    pub milliseconds: String,
}

fn de_time<'de, D>(de: D) -> Result<chrono::TimeDelta, D::Error>
where
    D: Deserializer<'de>,
{
    let input = String::deserialize(de)?;
    if let Ok(time) = chrono::NaiveTime::parse_from_str(&input, "%M:%S:%.3f") {
        Ok(time.signed_duration_since(chrono::NaiveTime::from_hms_opt(0, 0, 0).unwrap()))
    } else {
        Err(D::Error::custom("invalid time"))
    }
}
