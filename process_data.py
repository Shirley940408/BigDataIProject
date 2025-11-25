#%%

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, upper, concat_ws, when, regexp_replace, split, regexp_extract, coalesce, count, sum, avg, try_divide
from pyspark.sql import types
import unicodedata

spark = (
    SparkSession.builder
        .appName('Create Player Parquet Data Files')
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "8g")
        .config("spark.sql.files.maxPartitionBytes", "128m")
        .getOrCreate()
)

spark.sparkContext.setCheckpointDir('checkpoint')

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

# Generate NBAstats data
nbastats = spark.read.csv('datasets/raw_data/nbastats', schema=nbastats_schema_raw)

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

nbastats.checkpoint()

# Load Shotdetail
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

shotdetail = spark.read.csv('datasets/raw_data/shotdetail', schema=shotdetail_schema_raw, dateFormat="yyyyMMdd")

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

shotdetail.checkpoint()

# Create additional files for dashboards and fields later

# Create Players File
def normalize_ascii_py(name):
    if name is None:
        return None
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')

players1 = nbastats \
.select("PLAYER1_ID", "PLAYER1_NAME") \
.dropDuplicates(["PLAYER1_ID", "PLAYER1_NAME"]) \
.withColumnRenamed("PLAYER1_ID", "ID") \
.withColumnRenamed("PLAYER1_NAME", "Name")

players2 = nbastats \
.select("PLAYER2_ID", "PLAYER2_NAME") \
.dropDuplicates(["PLAYER2_ID", "PLAYER2_NAME"]) \
.filter(col("PLAYER2_ID") != "0") \
.withColumnRenamed("PLAYER2_ID", "ID") \
.withColumnRenamed("PLAYER2_NAME", "Name")

# UNION both lists
players = players1.unionByName(players2)
players = players.drop_duplicates(['ID'])

normalize_ascii = udf(normalize_ascii_py, types.StringType())

players = players.withColumn("Name", normalize_ascii(col("Name")))

players.write.mode("overwrite").format("csv").save("datasets/players")

# Create Teams File
teams = nbastats \
.select("PLAYER1_TEAM_ID", "PLAYER1_TEAM_CITY", "PLAYER1_TEAM_NICKNAME", "PLAYER1_TEAM_ABBREVIATION", "SEASON") \
.withColumnRenamed("PLAYER1_TEAM_ID", "ID") \
.withColumnRenamed("PLAYER1_TEAM_CITY", "City") \
.withColumnRenamed("PLAYER1_TEAM_NICKNAME", "Nickname") \
.withColumnRenamed("PLAYER1_TEAM_ABBREVIATION", "Abbreviation")\
.filter(col("ID") != "") \
.sort('SEASON', ascending=False) \
.drop("SEASON") \
.dropDuplicates(['Abbreviation'])
teams.checkpoint()
teams.write.mode("overwrite").format("csv").save("datasets/teams")

games = shotdetail.select("GAME_ID", "GAME_DATE", "HTM", "VTM").drop_duplicates(['GAME_ID'])


games = games.join(teams, games.HTM == teams.Abbreviation, how='inner') \
                .withColumnRenamed("ID", "HOME_ID") \
                .drop('City', 'Nickname', 'Abbreviation')

games = games.join(teams, games.VTM == teams.Abbreviation, how='inner') \
                .withColumnRenamed("ID", "AWAY_ID") \
                .drop('City', 'Nickname', 'Abbreviation') \
                .select('GAME_ID', 'GAME_DATE', 'HOME_ID', 'AWAY_ID')

games.checkpoint()
games.write.mode("overwrite").format("csv").save("datasets/games")

# Generate Column for Opponent
nbastats = nbastats.join(games, on = 'GAME_ID', how='inner')
nbastats = nbastats.withColumn("OPPONENT", when(col("PLAYER1_TEAM_ID") == col("HOME_ID"), col("AWAY_ID")).otherwise(col("HOME_ID")))

# Drop Unneeded Columns now that Additional Files and Fields generated
nbastats = nbastats.drop('PLAYER1_NAME', 'PLAYER2_NAME', 'PLAYER1_TEAM_CITY', 'PLAYER1_TEAM_NICKNAME', 'PLAYER1_TEAM_ABBREVIATION', 'HOME_ID', 'AWAY_ID')
shotdetail = shotdetail.drop('HTM', 'VTM', 'GAME_DATE')

nbastats.checkpoint()
shotdetail.checkpoint()

shotdetail = shotdetail.withColumnRenamed("GAME_ID", "SHOT_GAME_ID")

# Join NBAstats and Shotdetail
nbadata = nbastats.join(shotdetail, (nbastats.GAME_ID == shotdetail.SHOT_GAME_ID) & (nbastats.EVENTNUM == shotdetail.GAME_EVENT_ID), "left")
nbadata = nbadata.drop("SHOT_GAME_ID", "GAME_EVENT_ID")
nbadata.checkpoint()

# Write Files to Parquet
# Player1 data
nbadata.write \
    .mode("overwrite") \
    .partitionBy("PLAYER1_ID") \
    .parquet("datasets/player_data")

# Player2 data
nbadata.filter(col("PLAYER2_ID") != "") \
    .write \
    .mode("append") \
    .partitionBy("PLAYER2_ID") \
    .parquet("datasets/player_data")

# Season data
"""
nbadata.write \
    .mode("overwrite") \
    .partitionBy("SEASON") \
    .parquet("datasets/season_data")
"""

# Generate Totals
totals = nbadata.withColumn("POINTS", when((col("EVENTMSGTYPE") == 3) & (~col("DESCRIPTION").rlike("^MISS")), 1).otherwise(0)) \
                .withColumn("POINTS", when((col("SHOT_TYPE") == "3PT Field Goal") & (col("SHOT_MADE_FLAG") == True), 3).otherwise(col("POINTS"))) \
                .withColumn("POINTS", when((col("SHOT_TYPE") == "2PT Field Goal") & (col("SHOT_MADE_FLAG") == True), 2).otherwise(col("POINTS")))

totals.checkpoint()

# Totals for all stats where player is player1
player1_totals = totals.groupBy("SEASON", "PLAYER1_ID").agg(
    sum("POINTS").alias("POINTS"),
    sum(when(col("EVENTMSGTYPE") == 3, 1)).alias("FTA"),
    sum(when(col("EVENTMSGTYPE") < 3, 1)).alias("FGA"),
    avg(when(col("EVENTMSGTYPE") < 3, col('SHOT_DISTANCE'))).alias("SHOT_DISTANCE"),
    sum(when(col("EVENTMSGTYPE") == 5, 1)).alias("TOV")
).withColumnRenamed("PLAYER1_ID", "ID")

# Totals for all stats where player is player2
player2_totals = totals.filter((col("EVENTMSGTYPE") < 3) & (col("SHOT_MADE_FLAG") == True) & (col("PLAYER2_ID") != "")) \
                        .groupBy("SEASON", "PLAYER2_ID").agg(count("EVENTMSGTYPE").alias("AST")) \
                        .withColumnRenamed("SEASON", "SEASON2")

# Join Dataframes Together
totals = player1_totals.join(player2_totals, (player1_totals.SEASON == player2_totals.SEASON2) & (player1_totals.ID == player2_totals.PLAYER2_ID), "outer")

totals = totals.withColumn("SEASON", coalesce(totals["SEASON"], totals["SEASON2"])) \
                .withColumn("ID", coalesce(totals["ID"], totals["PLAYER2_ID"])) \
                .drop("SEASON2", "PLAYER2_ID") \
                .fillna(0)

# Create Columns for Stats
totals = totals.withColumn("PPP", try_divide(col("POINTS"), col("FGA") + 0.44 * col("FTA") + col("TOV"))) \
                .withColumn("TS%", try_divide(col("POINTS")*100,  2 * (col("FGA") + 0.44 * col("FTA")))) \
                .withColumn("AST/TOV", try_divide(col("AST"), col("TOV"))) \
                .withColumn("FTr", try_divide(col("FTA"), col("FGA"))) \
                .fillna(0)

# Write Totals to Parquet
totals.write.mode("overwrite").partitionBy("SEASON").parquet("datasets/totals")
#%%
