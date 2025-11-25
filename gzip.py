from pyspark.sql import SparkSession
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

nbastats = spark.read.csv('datasets/raw_data_old/nbastats', header=True, schema=nbastats_schema_raw)
nbastats.write.mode("overwrite").option("compression", "gzip").format("csv").save("datasets/raw_data/nbastats")


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
    types.StructField('GAME_DATE', types.StringType()),
    types.StructField('HTM', types.StringType()),
    types.StructField('VTM', types.StringType()),
])

shotdetail = spark.read.csv('datasets/raw_data_old/shotdetail', header=True, schema=shotdetail_schema_raw)
shotdetail.write.mode("overwrite").option("compression", "gzip").format("csv").save("datasets/raw_data/shotdetail")