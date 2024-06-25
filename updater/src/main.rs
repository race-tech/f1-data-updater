mod models;
mod tables;

fn main() -> anyhow::Result<()> {
    let url = "mysql://root:password@localhost:13306/f1db";
    let _ = mysql::Pool::new(url)?;

    Ok(())
}
