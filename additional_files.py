#%%

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, when, sum, avg, count, coalesce, try_divide
from pyspark.sql import types
import unicodedata
from nbastats import load_nbastats
from shotdetail import load_shotdetail

#spark = SparkSession.builder.appName('Create Additional Data Files').getOrCreate()
spark = (
    SparkSession.builder
        .appName('Create Additional Data Files')
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "8g")
        .config("spark.sql.files.maxPartitionBytes", "128m")
        .getOrCreate()
)

spark.sparkContext.setCheckpointDir('checkpoint')

# Function to remove accent characters from players names
def normalize_ascii_py(name):
    if name is None:
        return None
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')

# Create Function to Generate file of all player names and IDs
def generate_players(nbastats):
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

    return players

# TEAMS
def generate_teams(nbastats):
    teams = nbastats \
    .select("PLAYER1_TEAM_ID", "PLAYER1_TEAM_CITY", "PLAYER1_TEAM_NICKNAME", "PLAYER1_TEAM_ABBREVIATION", "SEASON") \
    .withColumnRenamed("PLAYER1_TEAM_ID", "ID") \
    .withColumnRenamed("PLAYER1_TEAM_CITY", "City") \
    .withColumnRenamed("PLAYER1_TEAM_NICKNAME", "Nickname") \
    .withColumnRenamed("PLAYER1_TEAM_ABBREVIATION", "Abbreviation")\
    .sort('SEASON', ascending=False) \
    .drop("SEASON") \
    .filter(col("ID") != "") \
    .dropDuplicates(['Abbreviation'])

    return teams

"""## Matchups"""
def generate_matches(shotdetail, teams):
    games = shotdetail.select("GAME_ID", "GAME_DATE", "HTM", "VTM").drop_duplicates(['GAME_ID'])

    games = games.join(teams, games.HTM == teams.Abbreviation, how='inner') \
                 .withColumnRenamed("ID", "HOME_ID") \
                 .drop('City', 'Nickname', 'Abbreviation')

    games = games.join(teams, games.VTM == teams.Abbreviation, how='inner') \
                 .withColumnRenamed("ID", "AWAY_ID") \
                 .drop('City', 'Nickname', 'Abbreviation') \
                 .select('GAME_ID', 'GAME_DATE', 'HOME_ID', 'AWAY_ID')

    return games

# Generate Totals for Each Season (Percentile Plots on Dashboard)
def generate_totals():
    nbadata_schema = types.StructType([
    types.StructField('GAME_ID', types.IntegerType()),
    types.StructField('EVENTNUM', types.IntegerType()),
    types.StructField('EVENTMSGTYPE', types.IntegerType()),
    types.StructField('PERIOD', types.IntegerType()),
    types.StructField('PCTIMESTRING', types.StringType()),
    types.StructField('DESCRIPTION', types.StringType()),
    types.StructField('SCOREMARGIN', types.IntegerType()),
    types.StructField('PLAYER1_ID', types.StringType()),
    types.StructField('PLAYER1_TEAM_ID', types.StringType()),
    types.StructField('PLAYER2_ID', types.StringType()),
    types.StructField('SEASON', types.IntegerType()),
    types.StructField('MINUTES', types.IntegerType()),
    types.StructField('SECONDS', types.IntegerType()),
    types.StructField('GAME_DATE', types.DateType()),
    types.StructField('OPPONENT', types.StringType()),  
    types.StructField('ACTION_TYPE', types.StringType()),
    types.StructField('SHOT_TYPE', types.StringType()),
    types.StructField('SHOT_ZONE_BASIC', types.StringType()),
    types.StructField('SHOT_ZONE_AREA', types.StringType()),
    types.StructField('SHOT_ZONE_RANGE', types.StringType()),
    types.StructField('SHOT_DISTANCE', types.IntegerType()),
    types.StructField('LOC_X', types.IntegerType()),
    types.StructField('LOC_Y', types.IntegerType()),
    types.StructField('SHOT_ATTEMPTED_FLAG', types.BooleanType()),
    types.StructField('SHOT_MADE_FLAG', types.BooleanType()),
    types.StructField('SHOT_METHOD', types.StringType()),
    types.StructField('ALLEY OOP', types.BooleanType()),
    types.StructField('BANK', types.BooleanType()),
    types.StructField('CUTTING', types.BooleanType()),
    types.StructField('DRIVING', types.BooleanType()),
    types.StructField('FLOATING', types.BooleanType()),
    types.StructField('PULLUP', types.BooleanType()),
    types.StructField('PUTBACK', types.BooleanType()),
    types.StructField('RUNNING', types.BooleanType()),
    types.StructField('REVERSE', types.BooleanType()),
    types.StructField('STEP BACK', types.BooleanType()),
    types.StructField('TIP', types.BooleanType()),
])
    # Load Data
    totals = spark.read.parquet('datasets/player_data', header=True, schema=nbadata_schema)

    # Point column calculation
    totals = totals.withColumn("POINTS", when((col("EVENTMSGTYPE") == 3) & (~col("DESCRIPTION").rlike("^MISS")), 1).otherwise(0)) \
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
    
    return totals


# Testing
"""
nbastats_schema_read = types.StructType([
    types.StructField('GAME_ID', types.IntegerType()),
    types.StructField('EVENTNUM', types.IntegerType()),
    types.StructField('EVENTMSGTYPE', types.IntegerType()),
    types.StructField('PERIOD', types.IntegerType()),
    types.StructField('PCTIMESTRING', types.StringType()),
    types.StructField('DESCRIPTION', types.StringType()),
    types.StructField('SCOREMARGIN', types.IntegerType()),
    types.StructField('PLAYER1_ID', types.StringType()),
    types.StructField('PLAYER1_NAME', types.StringType()),
    types.StructField('PLAYER1_TEAM_ID', types.StringType()),
    types.StructField('PLAYER1_TEAM_CITY', types.StringType()),
    types.StructField('PLAYER1_TEAM_NICKNAME', types.StringType()),
    types.StructField('PLAYER1_TEAM_ABBREVIATION', types.StringType()),
    types.StructField('PLAYER2_ID', types.StringType()),
    types.StructField('PLAYER2_NAME', types.StringType()),
    types.StructField('SEASON', types.IntegerType()),
    types.StructField('MINUTES', types.IntegerType()),
    types.StructField('SECONDS', types.IntegerType()),
])
nbastats = spark.read.csv('datasets/nbastats', schema=nbastats_schema_read)

shotdetail_schema_read = types.StructType([
    types.StructField('GAME_ID', types.IntegerType()),
    types.StructField('GAME_EVENT_ID', types.IntegerType()),
    types.StructField('ACTION_TYPE', types.StringType()),
    types.StructField('SHOT_TYPE', types.StringType()),
    types.StructField('SHOT_ZONE_BASIC', types.StringType()),
    types.StructField('SHOT_ZONE_AREA', types.StringType()),
    types.StructField('SHOT_ZONE_RANGE', types.StringType()),
    types.StructField('SHOT_DISTANCE', types.IntegerType()),
    types.StructField('LOC_X', types.IntegerType()),
    types.StructField('LOC_Y', types.IntegerType()),
    types.StructField('SHOT_ATTEMPTED_FLAG', types.BooleanType()),
    types.StructField('SHOT_MADE_FLAG', types.BooleanType()),
    types.StructField('SHOT_METHOD', types.StringType()),
    types.StructField('GAME_DATE', types.DateType()),
    types.StructField('HTM', types.StringType()),
    types.StructField('VTM', types.StringType()),
    types.StructField('ALLEY OOP', types.BooleanType()),
    types.StructField('BANK', types.BooleanType()),
    types.StructField('CUTTING', types.BooleanType()),
    types.StructField('DRIVING', types.BooleanType()),
    types.StructField('FLOATING', types.BooleanType()),
    types.StructField('PULLUP', types.BooleanType()),
    types.StructField('PUTBACK', types.BooleanType()),
    types.StructField('RUNNING', types.BooleanType()),
    types.StructField('REVERSE', types.BooleanType()),
    types.StructField('STEP BACK', types.BooleanType()),
    types.StructField('TIP', types.BooleanType()),
])
shotdetail = spark.read.csv('datasets/shotdetail', schema=shotdetail_schema_read, dateFormat="yyyy-MM-dd")
"""

#players = generate_players(nbastats)
#players.write.mode("overwrite").format("csv").save("datasets/players")

#teams = generate_teams(nbastats)
#teams.write.mode("overwrite").format("csv").save("datasets/teams")

#matches = generate_matches(shotdetail, teams)
#matches.write.mode("overwrite").format("csv").save("datasets/games")

totals = generate_totals()
totals.write.mode("overwrite").partitionBy("SEASON").parquet("datasets/totals")

#%%