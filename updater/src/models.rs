use serde::Deserialize;

#[derive(Deserialize)]
pub struct LapAnalysis {
    pub lap: u16,
    pub driver: u16,
    pub time: String,
    pub position: u16,
    pub milliseconds: String,
}

#[derive(Deserialize)]
pub struct QualificationOrder {
    pub pos: u16,
    pub no: u16,
    pub driver: String,
    pub entrant: String,
    pub q1: String,
    pub q1_laps: u32,
    #[serde(rename = "%")]
    pub pourcentage: f32,
    pub q1_time: String,
    pub q2: String,
    pub q2_laps: u32,
    pub q2_time: String,
    pub q3: String,
    pub q3_laps: u32,
    pub q3_time: String,
}

#[derive(Deserialize)]
pub struct DriverRaceResult {
    pub no: u16,
    pub entrant: String,
    pub grid: u16,
    pub position: u16,
    #[serde(rename = "positionOrder")]
    pub position_order: u16,
    pub points: u16,
    pub laps: u16,
    pub time: String,
    pub milliseconds: String,
    #[serde(rename = "fastestLap")]
    pub fastest_lap: u16,
    pub rank: u16,
    #[serde(rename = "fastestLapTime")]
    pub fatest_lap_time: String,
    #[serde(rename = "fastestLapSpeed")]
    pub fastest_lap_speed: f32,
}

#[derive(Deserialize)]
pub struct ConstructorRaceResult {
    pub constructor: String,
    pub points: u16,
}

#[derive(Deserialize)]
pub struct DriverChampionship {
    pub driver: String,
    pub points: u32,
    pub position: u32,
    pub wins: u32,
}

#[derive(Deserialize)]
pub struct ConstructorChampionship {
    pub constructor: String,
    pub points: u32,
    pub position: u32,
    pub wins: u32,
}

#[derive(Deserialize)]
pub struct PitStop {
    pub no: u16,
    pub driver: String,
    pub stop: u32,
    pub lap: u16,
    pub time: String,
    pub duration: String,
    pub milliseconds: String,
}