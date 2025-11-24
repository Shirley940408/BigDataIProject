#%%

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, upper, regexp_replace, regexp_extract
from pyspark.sql import types

spark = (
    SparkSession.builder
        .appName('Shotdetails')
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "8g")
        .config("spark.sql.files.maxPartitionBytes", "128m")
        .getOrCreate()
)


shotdetail_schema_raw = types.StructType([
    types.StructField('GRID_TYPE', types.StringType()),
    types.StructField('GAME_ID', types.IntegerType()),
    types.StructField('GAME_EVENT_ID', types.IntegerType()),
    types.StructField('PLAYER_ID', types.IntegerType()),
    types.StructField('PLAYER_NAME', types.StringType()),
    types.StructField('TEAM_ID', types.IntegerType()),
    types.StructField('TEAM_NAME', types.StringType()),
    types.StructField('PERIOD', types.IntegerType()),
    types.StructField('MINUTES_REMAINING', types.IntegerType()),
    types.StructField('SECONDS_REMAINING', types.IntegerType()),
    types.StructField('EVENT_TYPE', types.StringType()),
    types.StructField('ACTION_TYPE', types.StringType()),
    types.StructField('SHOT_TYPE', types.StringType()),
    types.StructField('SHOT_ZONE_BASIC', types.StringType()),
    types.StructField('SHOT_ZONE_AREA', types.StringType()),
    types.StructField('SHOT_ZONE_RANGE', types.StringType()),
    types.StructField('SHOT_DISTANCE', types.IntegerType()),
    types.StructField('LOC_X', types.IntegerType()),
    types.StructField('LOC_Y', types.IntegerType()),
    types.StructField('SHOT_ATTEMPTED_FLAG', types.IntegerType()),
    types.StructField('SHOT_MADE_FLAG', types.IntegerType()),
    types.StructField('GAME_DATE', types.DateType()),
    types.StructField('HTM', types.StringType()),
    types.StructField('VTM', types.StringType()),
])	



# Default of 29 partitions on load dont need to repartition
def load_shotdetail():
    shotdetail = spark.read.csv('datasets/raw_data/shotdetail', header=True, schema=shotdetail_schema_raw, dateFormat="yyyyMMdd")

    # Format Action Type Column
    shotdetail = shotdetail.withColumn('ACTION_TYPE', upper(shotdetail['ACTION_TYPE']))
    shotdetail = shotdetail.withColumn(
        "ACTION_TYPE",
        regexp_replace("ACTION_TYPE", "-", "")
    )

    # For Dashboard solving later
    """
    shotdetail = (
    shotdetail
    .withColumn(col, regexp_replace(col, "-", ""))
    .withColumn(col, regexp_replace(col, " ", "_"))
    .withColumn(col, regexp_replace(col, "/", ""))
    )
    """

    # Get Any Attributes in String (Driving, cutting, etc...) and the Shot Method (Jump Shot, Hook Shot, etc...)
    attributes_method_patttern = r"^(.*?)(\b\w+ SHOT)$"
    shotdetail = shotdetail.withColumn("SHOT_METHOD", regexp_extract(col("ACTION_TYPE"), attributes_method_patttern, 2)).withColumn("SHOT_ATTRIBUTES", regexp_extract(col("ACTION_TYPE"), attributes_method_patttern, 1))

    # Select Columns Needed
    shotdetail = shotdetail.select(
    "GAME_ID", "GAME_EVENT_ID", "ACTION_TYPE",
    "SHOT_TYPE", "SHOT_ZONE_BASIC", "SHOT_ZONE_AREA", "SHOT_ZONE_RANGE",
    "SHOT_DISTANCE", "LOC_X", "LOC_Y",
    "SHOT_ATTEMPTED_FLAG", "SHOT_MADE_FLAG",
    "SHOT_ATTRIBUTES", "SHOT_METHOD",
    "GAME_DATE", "HTM", "VTM"
    )

    # Change Shot Zones to be General Areas instead of specific ("Right Corner 3" is now just Corner Three)
    shotdetail = shotdetail.withColumn("SHOT_ZONE_BASIC", regexp_replace(col("SHOT_ZONE_BASIC"), "Left |Right ", ""))

    # Change Shot Zone Area to be more general by removing details from center
    shotdetail = shotdetail.withColumn("SHOT_ZONE_AREA", regexp_replace(col("SHOT_ZONE_AREA"), "Left Side Center\\(LC\\)", "Left Side")) \
                        .withColumn("SHOT_ZONE_AREA", regexp_replace(col("SHOT_ZONE_AREA"), "Right Side Center\\(RC\\)", "Right Side")) \
                        .withColumn("SHOT_ZONE_AREA", regexp_replace(col("SHOT_ZONE_AREA"), "\\(.*?\\)", ''))

    # Create Column For Each Attribute of Interest
    attr_cols = ["ALLEY OOP", "BANK", "CUTTING", "DRIVING", "FLOATING", "PULLUP", "PUTBACK", "RUNNING", "REVERSE", "STEP BACK", "TIP"]
    for attr in attr_cols:
        shotdetail = shotdetail.withColumn(
            attr,
            col("SHOT_ATTRIBUTES").contains(attr)
        )
    shotdetail = shotdetail.drop("SHOT_ATTRIBUTES")

    shotdetail = shotdetail.withColumn("SHOT_ATTEMPTED_FLAG", col("SHOT_ATTEMPTED_FLAG").cast("boolean"))
    shotdetail = shotdetail.withColumn("SHOT_MADE_FLAG", col("SHOT_MADE_FLAG").cast("boolean"))

    return shotdetail

# Default partitions are 29
# shotdetail = load_shotdetail()
# shotdetail.write.mode("overwrite").format("csv").save("datasets/shotdetail")
#%%