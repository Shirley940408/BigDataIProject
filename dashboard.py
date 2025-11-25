
#%% 
import streamlit as st
import numpy as np
import pandas as pd
import glob
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
import matplotlib as mpl
import seaborn as sns
from scipy import stats

def draw_court(ax=None, color='white', lw=2, outer_lines=False):
    # If an axes object isn't provided to plot onto, just get current one
    if ax is None:
        ax = plt.gca()

    # Create the various parts of an NBA basketball court

    # Create the basketball hoop
    # Diameter of a hoop is 18" so it has a radius of 9", which is a value
    # 7.5 in our coordinate system
    hoop = Circle((0, 0), radius=7.5, linewidth=lw, color=color, fill=False)

    # Create backboard
    backboard = Rectangle((-30, -7.5), 60, -1, linewidth=lw, color=color)

    # The paint
    # Create the outer box 0f the paint, width=16ft, height=19ft
    outer_box = Rectangle((-80, -47.5), 160, 190, linewidth=lw, color=color,
                          fill=False)
    # Create the inner box of the paint, widt=12ft, height=19ft
    inner_box = Rectangle((-60, -47.5), 120, 190, linewidth=lw, color=color,
                          fill=False)

    # Create free throw top arc
    top_free_throw = Arc((0, 142.5), 120, 120, theta1=0, theta2=180,
                         linewidth=lw, color=color, fill=False)
    # Create free throw bottom arc
    bottom_free_throw = Arc((0, 142.5), 120, 120, theta1=180, theta2=0,
                            linewidth=lw, color=color, linestyle='dashed')
    # Restricted Zone, it is an arc with 4ft radius from center of the hoop
    restricted = Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw,
                     color=color)

    # Three point line
    # Create the side 3pt lines, they are 14ft long before they begin to arc
    corner_three_a = Rectangle((-220, -47.5), 0, 140, linewidth=lw,
                               color=color)
    corner_three_b = Rectangle((220, -47.5), 0, 140, linewidth=lw, color=color)
    # 3pt arc - center of arc will be the hoop, arc is 23'9" away from hoop
    # I just played around with the theta values until they lined up with the 
    # threes
    three_arc = Arc((0, 0), 475, 475, theta1=22, theta2=158, linewidth=lw,
                    color=color)

    # Center Court
    center_outer_arc = Arc((0, 422.5), 120, 120, theta1=180, theta2=0,
                           linewidth=lw, color=color)
    center_inner_arc = Arc((0, 422.5), 40, 40, theta1=180, theta2=0,
                           linewidth=lw, color=color)

    # List of the court elements to be plotted onto the axes
    court_elements = [hoop, backboard, outer_box, inner_box, top_free_throw,
                      bottom_free_throw, restricted, corner_three_a,
                      corner_three_b, three_arc, center_outer_arc,
                      center_inner_arc]

    if outer_lines:
        # Draw the half court line, baseline and side out bound lines
        outer_lines = Rectangle((-250, -47.5), 500, 470, linewidth=lw,
                                color=color, fill=False)
        court_elements.append(outer_lines)

    # Add the court elements onto the axes
    for element in court_elements:
        ax.add_patch(element)
    
    return ax


st.set_page_config(layout = 'wide')
# Streamlit layout settings
tab1, tab2, tab3 = st.tabs(["Shooting Filtered", "Other Shooting", "Ball Handling"])

players_schema = {
    'ID': str,
    'name': str
}

file_path = glob.glob('players/*.csv' )
players = []
for file in file_path:
    players.append(pd.read_csv(file, names=['ID', 'Name'], dtype=players_schema))

players = pd.concat(players)
players = players.dropna()

# Filter Players to be sample only
player_list = ['893', '252', '406', '947', '1495', '708', '959', '1717', '977', '2544', '201565', '201142', '201939', '201566', '201935', '203507', '203999', '203954', '1628983']
players = players[players['ID'].isin(player_list)]
players['select'] = players['Name'] + ' | ' + players['ID']
player = st.sidebar.selectbox("Select Player", players['select'], key='player')
player = player.split(' | ')[1]

# Filter Opponent
teams_schema = {
    'ID': str,
    'City': str,
    'Nickname': str,
    'Abbreviation': str
}

file_path = glob.glob('teams/*.csv' )
teams = []
for file in file_path:
    teams.append(pd.read_csv(file, names=['ID', 'City', 'Nickname', 'Abbreviation'], dtype=teams_schema))

teams = pd.concat(teams)
teams = teams.dropna()
teams['select'] = teams['Abbreviation'] + ' | ' + teams['ID']
teams_list = np.insert(teams['select'], 0, "ALL")
opponent = st.sidebar.selectbox("Select Opponent", teams_list, key='opponent')

if player:
    file_path = glob.glob('player_data/PLAYER1_ID=' + player + '/*' )
    player_data1 = pd.read_parquet(file_path)

# Filter By Season
seasons = np.sort(player_data1['SEASON'].unique())
season = st.sidebar.selectbox("Select Season", seasons, key='season')
player_data1 =  player_data1[player_data1['SEASON'] == int(season)]

# Get Perecentiles
file_path = glob.glob('totals/SEASON=' + str(season) + '/*' )
percentiles_data = pd.read_parquet(file_path)
player_percentiles = percentiles_data[percentiles_data['ID'] == player]

# Create Colour Mapping
cmap = plt.cm.coolwarm
norm = mpl.colors.Normalize(vmin=0, vmax=100)

sns.set_style(rc={'axes.facecolor': '#262730', 'figure.facecolor': '#262730', 'text.color': 'white', 'axes.labelcolor': 'white', 
                'axes.grid': False, 'xtick.color': 'white', 'ytick.color': 'white'})

def plot_percentile(stat, value, series):
    rank = round(stats.percentileofscore(series, value, kind='rank'),0)
    colour = mpl.colors.to_hex(cmap(norm(rank)))

    st.sidebar.write(stat)

    plot = sns.displot(x=series, kind="kde", color=colour, fill=True, bw_adjust=2, height=1.5, aspect = 3)
    plt.axvline(value, color='white', linestyle='-', linewidth=2, label=f'Value: {value} \nPercentile: {rank}')
    plt.ylabel(None)
    plt.xlabel(None)
    plt.legend(fontsize=11, handlelength=0)
    plt.xlim(left=0)
    st.sidebar.pyplot(plot)

for stat in ['SHOT_DISTANCE', 'PPP', 'TS%', 'AST/TOV', 'FTr']:
    value = round(player_percentiles[stat].values[0],2)
    plot_percentile(stat, value, percentiles_data[stat])

# MAKE SIDE BAR PERCENTILE CHARTS HERE
with tab1:
    col1, col2 = st.columns([0.5, 0.5])

    # Select All Shot Rows
    player_shots = player_data1[player_data1['EVENTMSGTYPE'] <= 2]
    player_shots_raw = player_shots.copy()

    #Filter by Opponent
    if opponent != 'ALL':
        opponent = opponent.split(' | ')[1]
        player_shots = player_shots[player_shots['OPPONENT'] == int(opponent)]

    # Filter by Dates
    if len(player_shots) > 0:
        date_range = col2.slider(
            "Select a Date Range",
            min_value=player_shots['GAME_DATE'].min(), #.to_pydatetime()
            max_value=player_shots['GAME_DATE'].max(), #.to_pydatetime()
            value=(player_shots['GAME_DATE'].min(), player_shots['GAME_DATE'].max()),
            key='date'
        )
        player_shots = player_shots[player_shots['GAME_DATE'] <= date_range[1]]
        player_shots = player_shots[player_shots['GAME_DATE'] >= date_range[0]]

    # Filter Shot Methods
    method_list = np.insert(player_shots['SHOT_METHOD'].unique(), 0, "ALL")
    method = col2.selectbox("Select Shot Method", method_list, key='method')
    if method != "ALL":
        player_shots = player_shots[player_shots['SHOT_METHOD'] == method]

    # Filter by a Shot attribute
    attributes_list = ["ALL", "ALLEY OOP", "BANK", "CUTTING", "DRIVING", "FLOATING", "PULLUP", "PUTBACK", "RUNNING", "REVERSE", "STEP BACK", "TIP"]
    attribute = col2.selectbox("Select Shot Attribute", attributes_list, key='attribute')
    if attribute != "ALL":
        player_shots = player_shots[player_shots[attribute]]

    # Filter Shot Type (2 or 3)
    shot_type_list = np.insert(player_shots['SHOT_TYPE'].unique(), 0, "ALL")
    shot_type = col2.selectbox("Select Shot Type (2 or 3)", shot_type_list, key='shot_score')
    if shot_type != "ALL":
        player_shots = player_shots[player_shots['SHOT_TYPE'] == shot_type]

    # Filter Shot Zone
    shot_zone_list = np.insert(player_shots['SHOT_ZONE_BASIC'].unique(), 0, "ALL")
    shot_zone = col2.selectbox("Select Shot Zone", shot_zone_list, key='shot_zone')
    if shot_zone != "ALL":
        player_shots = player_shots[player_shots['SHOT_ZONE_BASIC'] == shot_zone]

    # Filter Shot Zone
    shot_area_list = np.insert(player_shots['SHOT_ZONE_AREA'].unique(), 0, "ALL")
    shot_zone_side = col2.selectbox("Select Shot Zone Side", shot_area_list, key='shot_side')
    if shot_zone_side != "ALL":
        player_shots = player_shots[player_shots['SHOT_ZONE_AREA'] == shot_zone_side]

    #Filter Shot Distance
    if len(player_shots) > 1:
        shot_distance = col2.slider(
            "Select Shot Distance",
            min_value=player_shots['SHOT_DISTANCE'].min(),
            max_value=player_shots['SHOT_DISTANCE'].max(),
            value=(player_shots['SHOT_DISTANCE'].min(), player_shots['SHOT_DISTANCE'].max())
        )
        player_shots = player_shots[player_shots['SHOT_DISTANCE'] <= shot_distance[1]]
        player_shots = player_shots[player_shots['SHOT_DISTANCE'] >= shot_distance[0]]

    # Filter Assisted
    assist_list = ["ALL", "ASSISTED", "UNASSISTED"]
    attribute = col2.selectbox("Select if Shot was Assisted", assist_list, key='assisted')
    if attribute != "ALL":
        if attribute == "ASSISTED":
            player_shots = player_shots[(player_shots['PLAYER2_ID'] != '') & (player_shots['SHOT_MADE_FLAG'] == 1)]
        else:
            player_shots = player_shots[(player_shots['PLAYER2_ID'] == '') & (player_shots['SHOT_MADE_FLAG'] == 1)]

    # Filter Made or Missed
    assist_list = ["ALL", "MADE", "MISSED"]
    attribute = col2.selectbox("Select if Shot was Made/Missed", assist_list, key='made_missed')
    if attribute != "ALL":
        if attribute == "MADE":
            player_shots = player_shots[player_shots['SHOT_MADE_FLAG'] == 1]
        else:
            player_shots = player_shots[player_shots['SHOT_MADE_FLAG'] == 0]

    
    # PLOTTING 
    def get_percent(values):
        return np.mean(values)*100

    player_shots['SHOT_MADE_FLAG'] = player_shots['SHOT_MADE_FLAG'].astype('bool')

    # Filter Type of Chart Shown
    plot_type = col1.selectbox("Select Chart Type", ['Scatter', 'Hexbin'])

    if plot_type == 'Scatter':
        plt.figure(figsize=(12,11))
        scatter_plot = plt.scatter(player_shots['LOC_X'], player_shots['LOC_Y'], c=player_shots['SHOT_MADE_FLAG'], cmap='coolwarm', s=50)
        draw_court(outer_lines=True)
        cbar = plt.colorbar(scatter_plot, ticks=[0, 1])
        cbar.set_ticklabels(['Miss', 'Make'])
        plt.xlim(-275, 275)
        plt.ylim(-75, 450)
        plt.axis('off')

        if len(player_shots) > 0:
            percent = round(player_shots['SHOT_MADE_FLAG'].sum()/player_shots['SHOT_ATTEMPTED_FLAG'].sum()*100, 2)
            plt.text(-275, 450, "FG: " + str(percent) + "%", fontsize=16)

        col1.pyplot(plt)
    else:
        min_bin = max(round(len(player_shots)*0.005), 1)
        plt.figure(figsize=(12,11))
        scatter_plot = plt.hexbin(player_shots['LOC_X'], player_shots['LOC_Y'], mincnt=min_bin, C=player_shots['SHOT_MADE_FLAG'], gridsize=15, vmin=0, vmax=100, reduce_C_function=get_percent, cmap='coolwarm')  
        draw_court(outer_lines=True)
        plt.colorbar(scatter_plot, label='FG %')
        plt.xlim(-275,275)
        plt.ylim(-75, 450)
        plt.axis('off')
        
        if len(player_shots) > 0:
            percent = round(player_shots['SHOT_MADE_FLAG'].sum()/player_shots['SHOT_ATTEMPTED_FLAG'].sum()*100, 2)
            plt.text(-275, 450, "FG: " + str(percent) + "%", fontsize=16)
            plt.text(-275, -75, "Minimum shots per bin: " + str(min_bin), fontsize=16)

        col1.pyplot(plt)
        

    st.dataframe(player_shots)

with tab2:
    # PLOT SHOT METHOD vs ATTRIBUTE

    player_shot_totals = player_shots_raw[['SHOT_ATTEMPTED_FLAG', "SHOT_MADE_FLAG", "SHOT_METHOD", "ALLEY OOP", "BANK", "CUTTING", "DRIVING", "FLOATING", "PULLUP", "PUTBACK", "RUNNING", "REVERSE", "STEP BACK", "TIP"]]

    fga = pd.melt(player_shot_totals, id_vars=['SHOT_METHOD'], value_vars=["ALLEY OOP", "BANK", "CUTTING", "DRIVING", "FLOATING", "PULLUP", "PUTBACK", "RUNNING", "REVERSE", "STEP BACK", "TIP"])
    fga = fga[fga['value']]
    fga = fga.rename(columns={'SHOT_METHOD': 'METHOD', 'variable': 'ATTRIBUTE', 'value': 'FGA'})
    fga = fga.groupby(['METHOD', 'ATTRIBUTE']).sum()

    fgm = pd.melt(player_shot_totals[player_shot_totals['SHOT_MADE_FLAG']], id_vars=['SHOT_METHOD'], value_vars=["ALLEY OOP", "BANK", "CUTTING", "DRIVING", "FLOATING", "PULLUP", "PUTBACK", "RUNNING", "REVERSE", "STEP BACK", "TIP"])
    fgm = fgm[fgm['value']]
    fgm = fgm.rename(columns={'SHOT_METHOD': 'METHOD', 'variable': 'ATTRIBUTE', 'value': 'FGM'})
    fgm = fgm.groupby(['METHOD', 'ATTRIBUTE']).sum()

    shot_totals = pd.merge(fga, fgm, how = 'left', on=['METHOD', 'ATTRIBUTE']).fillna(0).astype(int)
    shot_totals['FG%'] = round(shot_totals['FGM']/shot_totals['FGA']*100,2)
    shot_totals['FGA%'] = shot_totals['FGA']/player_shot_totals['SHOT_ATTEMPTED_FLAG'].sum()*100

    fig = sns.relplot(data=shot_totals, x='ATTRIBUTE', y='METHOD', hue='FG%', hue_norm=(0, 100), size='FGA%', palette='coolwarm', height=4, aspect = 3, sizes=(50, 500))
    plt.xticks(rotation=90)
    st.pyplot(fig)
# %%

# To Do 
# USE FFILL in pandas on small datafframe for Scoremargin
# #nbastats['SCOREMARGIN'] = nbastats['SCOREMARGIN'].str.replace("TIE", "0")
# Score Margin Filter
# Minutes Filter
# Checkbox to show numbers in hex bin



# SHOW FG% based on filtered data shown