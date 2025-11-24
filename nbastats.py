#%%

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat_ws, when, regexp_replace, split
from pyspark.sql import types

spark = (
    SparkSession.builder
        .appName('NBAStats')
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "8g")
        .config("spark.sql.files.maxPartitionBytes", "128m")
        .getOrCreate()
)

nbastats_schema_raw = types.StructType([
    types.StructField('GAME_ID', types.IntegerType()),
    types.StructField('EVENTNUM', types.IntegerType()),
    types.StructField('EVENTMSGTYPE', types.IntegerType()),
    types.StructField('EVENTMSGACTIONTYPE', types.IntegerType()),
    types.StructField('PERIOD', types.IntegerType()),
    types.StructField('WCTIMESTRING', types.StringType()),
    types.StructField('PCTIMESTRING', types.StringType()),
    types.StructField('HOMEDESCRIPTION', types.StringType()),
    types.StructField('NEUTRALDESCRIPTION', types.StringType()),
    types.StructField('VISITORDESCRIPTION', types.StringType()),
    types.StructField('SCORE', types.StringType()),
    types.StructField('SCOREMARGIN', types.IntegerType()),
    types.StructField('PERSON1TYPE', types.IntegerType()),
    types.StructField('PLAYER1_ID', types.StringType()),
    types.StructField('PLAYER1_NAME', types.StringType()),
    types.StructField('PLAYER1_TEAM_ID', types.StringType()),
    types.StructField('PLAYER1_TEAM_CITY', types.StringType()),
    types.StructField('PLAYER1_TEAM_NICKNAME', types.StringType()),
    types.StructField('PLAYER1_TEAM_ABBREVIATION', types.StringType()),
    types.StructField('PERSON2TYPE', types.IntegerType()),
    types.StructField('PLAYER2_ID', types.StringType()),
    types.StructField('PLAYER2_NAME', types.StringType()),
    types.StructField('PLAYER2_TEAM_ID', types.StringType()),
    types.StructField('PLAYER2_TEAM_CITY', types.StringType()),
    types.StructField('PLAYER2_TEAM_NICKNAME', types.StringType()),
    types.StructField('PLAYER2_TEAM_ABBREVIATION', types.StringType()),
    types.StructField('PERSON3TYPE', types.IntegerType()),
    types.StructField('PLAYER3_ID', types.StringType()),
    types.StructField('PLAYER3_NAME', types.StringType()),
    types.StructField('PLAYER3_TEAM_ID', types.StringType()),
    types.StructField('PLAYER3_TEAM_CITY', types.StringType()),
    types.StructField('PLAYER3_TEAM_NICKNAME', types.StringType()),
    types.StructField('PLAYER3_TEAM_ABBREVIATION', types.StringType()),
    types.StructField('VIDEO_AVAILABLE_FLAG', types.IntegerType()),
    types.StructField('SEASON', types.IntegerType()),
])

# Default of 29 partitions on load dont need to repartition
def load_nbastats():
    nbastats = spark.read.csv('datasets/raw_data/nbastats', header=True, schema=nbastats_schema_raw)

    # Filter play events
    nbastats = nbastats.filter(
        (col('EVENTMSGTYPE') <= 5) & (col('EVENTMSGTYPE') != 4)
    )

    # Create Description Column
    nbastats = nbastats.withColumn("DESCRIPTION",concat_ws("", nbastats["HOMEDESCRIPTION"], nbastats["NEUTRALDESCRIPTION"], nbastats["VISITORDESCRIPTION"]))

    # Move Player 3 IDs to Player 2 when the play has a block
    mask = col("DESCRIPTION").contains(' BLK)')

    nbastats = nbastats \
        .withColumn("PERSON2TYPE", when(mask, col("PERSON3TYPE")).otherwise(col("PERSON2TYPE"))) \
        .withColumn("PERSON2_ID", when(mask, col("PLAYER3_ID")).otherwise(col("PLAYER2_ID"))) \
        .withColumn("PERSON2_NAME", when(mask, col("PLAYER3_NAME")).otherwise(col("PLAYER2_NAME"))) \
        .withColumn("PERSON2_TEAM_ID", when(mask, col("PLAYER3_TEAM_ID")).otherwise(col("PLAYER2_TEAM_ID")))

    # Select final columns
    nbastats = nbastats.select(
        "GAME_ID", "EVENTNUM", "EVENTMSGTYPE", "PERIOD", "PCTIMESTRING", "DESCRIPTION", "SCOREMARGIN", "PLAYER1_ID", "PLAYER1_NAME", 
        "PLAYER1_TEAM_ID", "PLAYER1_TEAM_CITY", "PLAYER1_TEAM_NICKNAME", "PLAYER1_TEAM_ABBREVIATION", "PLAYER2_ID", "PLAYER2_NAME", "SEASON"
    )

    #Removing Trailing Decimals on TeamID on load
    nbastats = nbastats.withColumn("PLAYER1_TEAM_ID", regexp_replace("PLAYER1_TEAM_ID", ".0", ""))

    # Split time to minutes and seconds
    nbastats = nbastats \
        .withColumn("MINUTES", split(col("PCTIMESTRING"), ":").getItem(0).cast("int")) \
        .withColumn("SECONDS", split(col("PCTIMESTRING"), ":").getItem(1).cast("int"))

    # Clean Fill NULLs with empty string 
    nbastats = nbastats.filter(col("PLAYER1_TEAM_ID").isNotNull())

    nbastats = nbastats.withColumn(
        "PLAYER2_ID",
        regexp_replace(col("PLAYER2_ID"), r"^0$", "")
    )
        
    return nbastats

# Testing Function - Default partitions are 29
# nbastats = load_nbastats()
# nbastats.write.mode("overwrite").format("csv").save("datasets/nbastats")


#%%