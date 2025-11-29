
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
import plotly.express as px
import plotly.graph_objects as go


# Funciton to Create a Half Court for scatter and hexbin plots
# From https://github.com/bradleyfay/py-Goldsberry/blob/main/docs/Visualizing%20NBA%20Shots%20with%20py-Goldsberry.ipynb
def draw_court(ax=None, color='white', lw=2, outer_lines=False):
    # If an axes object isn't provided to plot onto, just get current one
    if ax is None:
        ax = plt.gca()

    # Create the various parts of an NBA basketball court

    # Create the basketball hoop
    # Diameter of a hoop is 18' so it has a radius of 9', which is a value
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
    # 3pt arc - center of arc will be the hoop, arc is 23'9' away from hoop
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


# Set Streamlit page Layout
st.set_page_config(layout = 'wide')
tab1, tab2 = st.tabs(['Shooting', 'Ball Handling'])

# Set Schema for loading the list of all players
players_schema = {
    'ID': str,
    'name': str
}

# Get the players files
file_path = glob.glob('players/*.csv' )
players = []
for file in file_path:
    players.append(pd.read_csv(file, names=['ID', 'Name'], dtype=players_schema))

# Concat all the dataframes read from files
players = pd.concat(players)
players = players.dropna()

# Create column for sleect box 
players['select'] = players['Name'] + ' | ' + players['ID']
players = players.sort_values(by='ID', key=pd.to_numeric)
player = st.sidebar.selectbox('Select Player', players['select'], key='player')
# Assign values from selectbox player
player_name, player_id = player.split(' | ')

#Get data for player select for both ID columns
file_path = glob.glob('player_data/PLAYER1_ID=' + player_id + '/*' )
player_data1 = pd.read_parquet(file_path)
file_path = glob.glob('player_data/PLAYER2_ID=' + player_id + '/*' )
player_data2 = pd.read_parquet(file_path)



# # Load Files for Team Information
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
teams = teams.drop_duplicates(['ID'])

# Create Column for opponent select box 
teams['select'] = teams['Abbreviation'] + ' | ' + teams['ID']
teams_list = np.insert(teams['select'], 0, 'ALL')
opponent = st.sidebar.selectbox('Select Opponent', teams_list, key='opponent')

#Filter Dataframes by Opponent
if opponent != 'ALL':
    opponent = opponent.split(' | ')[1]
    player_data1 = player_data1[player_data1['OPPONENT'] == opponent]
    player_data2 = player_data2[player_data2['OPPONENT'] == opponent]

# Filter Dataframes By Season
seasons = np.sort(player_data1['SEASON'].unique())
season = st.sidebar.selectbox('Select Season', seasons, key='season')
player_data1 =  player_data1[player_data1['SEASON'] == int(season)]
player_data2 =  player_data2[player_data2['SEASON'] == int(season)]

# Get Perecentile data files based on season select
file_path = glob.glob('totals/SEASON=' + str(season) + '/*' )
percentiles_data = pd.read_parquet(file_path)
player_percentiles = percentiles_data[percentiles_data['ID'] == player_id]

# Create Colour Mapping for percentile plots
cmap = plt.cm.coolwarm
norm = mpl.colors.Normalize(vmin=0, vmax=100)

# Define Style for plots
sns.set_style(rc={'axes.facecolor': '#262730', 'figure.facecolor': '#262730', 'text.color': 'white', 'axes.labelcolor': 'white', 
                'axes.grid': False, 'xtick.color': 'white', 'ytick.color': 'white'})

# Create Function to plot the percentile values
def plot_percentile(stat, value, series):
    # Get Percentile value and colour for stat
    rank = round(stats.percentileofscore(series, value, kind='rank'),0)
    colour = mpl.colors.to_hex(cmap(norm(rank)))
    st.sidebar.write(stat)

    # Display the KDE plot with an axline where the value is
    plot = sns.displot(x=series, kind='kde', color=colour, fill=True, bw_adjust=2, height=1.5, aspect = 3)
    plt.axvline(value, color='white', linestyle='-', linewidth=2, label=f'Value: {value} \nPercentile: {rank}')
    plt.ylabel(None)
    plt.xlabel(None)
    plt.legend(fontsize=11, handlelength=0)
    plt.xlim(left=0)
    st.sidebar.pyplot(plot)

# Plot each percentile value in KDE plots with function declared above
for stat in ['SHOT_DISTANCE', 'PPP', 'TS%', 'AST/TOV', 'FTr']:
    value = round(player_percentiles[stat].values[0],2)
    plot_percentile(stat, value, percentiles_data[stat])

# PLots for First Tab of dashboard
with tab1:
    col1, col2 = st.columns([0.5, 0.5])

    # Select All Rows where a shot was attempted
    player_shots = player_data1[player_data1['EVENTMSGTYPE'] <= 2]
    player_shots_raw = player_shots.copy()

    # Create Game Date slider if there is at least 2 games in the date range
    if len(player_shots['GAME_DATE'].unique()) > 1:
        date_range = col2.slider(
            'Select a Date Range',
            min_value=player_shots['GAME_DATE'].min(), #.to_pydatetime()
            max_value=player_shots['GAME_DATE'].max(), #.to_pydatetime()
            value=(player_shots['GAME_DATE'].min(), player_shots['GAME_DATE'].max()),
            key='date'
        )
        # Filter by dates on slider
        player_shots = player_shots[player_shots['GAME_DATE'] <= date_range[1]]
        player_shots = player_shots[player_shots['GAME_DATE'] >= date_range[0]]

    # Filter Shot Methods
    method_list = np.insert(player_shots['SHOT_METHOD'].unique(), 0, 'ALL')
    method = col2.selectbox('Select Shot Method', method_list, key='method')
    if method != 'ALL':
        player_shots = player_shots[player_shots['SHOT_METHOD'] == method]

    # Filter by a Shot attribute
    attributes_list = ['ALL', 'ALLEY OOP', 'BANK', 'CUTTING', 'DRIVING', 'FLOATING', 'PULLUP', 'PUTBACK', 'RUNNING', 'REVERSE', 'STEP BACK', 'TIP']
    attribute = col2.selectbox('Select Shot Attribute', attributes_list, key='attribute')
    if attribute != 'ALL':
        player_shots = player_shots[player_shots[attribute]]

    # Filter Shot Type (2pt or 3pt)
    shot_type_list = np.insert(player_shots['SHOT_TYPE'].unique(), 0, 'ALL')
    shot_type = col2.selectbox('Select Shot Type (2 or 3)', shot_type_list, key='shot_score')
    if shot_type != 'ALL':
        player_shots = player_shots[player_shots['SHOT_TYPE'] == shot_type]

    # Filter Shot Zone
    shot_zone_list = np.insert(player_shots['SHOT_ZONE_BASIC'].unique(), 0, 'ALL')
    shot_zone = col2.selectbox('Select Shot Zone', shot_zone_list, key='shot_zone')
    if shot_zone != 'ALL':
        player_shots = player_shots[player_shots['SHOT_ZONE_BASIC'] == shot_zone]

    # Filter Shot Zone
    shot_area_list = np.insert(player_shots['SHOT_ZONE_AREA'].unique(), 0, 'ALL')
    shot_zone_side = col2.selectbox('Select Shot Zone Side', shot_area_list, key='shot_side')
    if shot_zone_side != 'ALL':
        player_shots = player_shots[player_shots['SHOT_ZONE_AREA'] == shot_zone_side]

    #Filter Shot Distance
    if len(player_shots) > 1:
        shot_distance = col2.slider(
            'Select Shot Distance',
            min_value=player_shots['SHOT_DISTANCE'].min(),
            max_value=player_shots['SHOT_DISTANCE'].max(),
            value=(player_shots['SHOT_DISTANCE'].min(), player_shots['SHOT_DISTANCE'].max())
        )
        player_shots = player_shots[player_shots['SHOT_DISTANCE'] <= shot_distance[1]]
        player_shots = player_shots[player_shots['SHOT_DISTANCE'] >= shot_distance[0]]

    # Filter Assisted
    assist_list = ['ALL', 'ASSISTED', 'UNASSISTED']
    attribute = col2.selectbox('Select if Shot was Assisted', assist_list, key='assisted')
    if attribute != 'ALL':
        if attribute == 'ASSISTED':
            player_shots = player_shots[(player_shots['PLAYER2_ID'] != '') & (player_shots['SHOT_MADE_FLAG'] == 1)]
        else:
            player_shots = player_shots[(player_shots['PLAYER2_ID'] == '') & (player_shots['SHOT_MADE_FLAG'] == 1)]

    # Filter Made or Missed
    assist_list = ['ALL', 'MADE', 'MISSED']
    attribute = col2.selectbox('Select if Shot was Made/Missed', assist_list, key='made_missed')
    if attribute != 'ALL':
        if attribute == 'MADE':
            player_shots = player_shots[player_shots['SHOT_MADE_FLAG'] == 1]
        else:
            player_shots = player_shots[player_shots['SHOT_MADE_FLAG'] == 0]

    
    # Change Data type for visualizations
    player_shots['SHOT_MADE_FLAG'] = player_shots['SHOT_MADE_FLAG'].astype('bool')

    # Filter Type of Chart Shown
    plot_type = col1.selectbox('Select Chart Type', ['Scatter', 'Hexbin'])

    # Plot the scatter plot
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
            plt.text(-275, 450, 'FG: ' + str(percent) + '%', fontsize=16)

        col1.pyplot(plt)
    # Plot the Hexbin plot
    else:
        # Reduce C function used for hexbins
        def get_percent(values):
            return np.mean(values)*100
        
        # Get the minimum number of shots for a bin to be displayed
        min_bin = max(round(len(player_shots)*0.005), 1)

        # Dummy plot to get bin count values
        dummy_plot = plt.hexbin(player_shots['LOC_X'], player_shots['LOC_Y'], mincnt=min_bin, gridsize=15)  
        # Get Counts and location of bins
        counts = dummy_plot.get_array()
        locations = dummy_plot.get_offsets()
        plt.close()

        # Plot the real Hexbin plot
        plt.figure(figsize=(12,11))
        scatter_plot = plt.hexbin(player_shots['LOC_X'], player_shots['LOC_Y'], mincnt=min_bin, C=player_shots['SHOT_MADE_FLAG'], gridsize=15, vmin=0, vmax=100, reduce_C_function=get_percent, cmap='coolwarm')  
        draw_court(outer_lines=True)
        plt.colorbar(scatter_plot, label='FG %')
        plt.xlim(-275,275)
        plt.ylim(-75, 450)
        plt.axis('off')
        
        # Get the FG% of the shots in the dataframe and display on plot
        if len(player_shots) > 0:
            percent = round(player_shots['SHOT_MADE_FLAG'].sum()/player_shots['SHOT_ATTEMPTED_FLAG'].sum()*100, 2)
            plt.text(-275, 450, 'FG: ' + str(percent) + '%', fontsize=16)
            plt.text(-275, -75, 'Minimum shots per bin: ' + str(min_bin), fontsize=16)

        # Using Dummy plot earlier display the count of shots in each bin
        for i, count in enumerate(counts):
            if count > 0:
                plt.text(locations[i, 0], locations[i, 1], int(count),
                        ha='center', va='center', color='black', fontsize=8)

        # Display the plot
        col1.pyplot(plt)

    # Create a divider and new column widths for treemap plot
    st.divider()
    col3, col4 = st.columns([0.3, 0.7])

    if len(player_shots) > 0:
        # Select Columns and add a new column if a shot has no attributes
        player_shot_totals = player_shots[['SHOT_ATTEMPTED_FLAG', 'SHOT_MADE_FLAG', 'SHOT_METHOD', 'ALLEY OOP', 'BANK', 'CUTTING', 'DRIVING', 'FLOATING', 'PULLUP', 'PUTBACK', 'RUNNING', 'REVERSE', 'STEP BACK', 'TIP']]
        player_shot_totals = player_shot_totals.dropna()
        player_shot_totals['NO ATTRIBUTE'] = ~(player_shot_totals[['ALLEY OOP', 'BANK', 'CUTTING', 'DRIVING', 'FLOATING', 'PULLUP', 'PUTBACK', 'RUNNING', 'REVERSE', 'STEP BACK', 'TIP']].any(axis=1))

        # Get the total count of shots for each shot method
        shots_grouped = player_shot_totals.groupby('SHOT_METHOD')['SHOT_ATTEMPTED_FLAG'].count().reset_index()

        # Get the number of shots attmped for each unique combo of shot method and attribute
        fga = pd.melt(player_shot_totals, id_vars=['SHOT_METHOD'], value_vars=['ALLEY OOP', 'BANK', 'CUTTING', 'DRIVING', 'FLOATING', 'PULLUP', 'PUTBACK', 'RUNNING', 'REVERSE', 'STEP BACK', 'TIP', 'NO ATTRIBUTE'])
        fga = fga[fga['value']]
        fga = fga.rename(columns={'SHOT_METHOD': 'METHOD', 'variable': 'ATTRIBUTE', 'value': 'FGA'})
        fga = fga.groupby(['METHOD', 'ATTRIBUTE']).sum()
        
        # Get the number of shots made for each unique combo of shot method and attribute
        fgm = pd.melt(player_shot_totals[player_shot_totals['SHOT_MADE_FLAG']], id_vars=['SHOT_METHOD'], value_vars=['ALLEY OOP', 'BANK', 'CUTTING', 'DRIVING', 'FLOATING', 'PULLUP', 'PUTBACK', 'RUNNING', 'REVERSE', 'STEP BACK', 'TIP', 'NO ATTRIBUTE'])
        if len(fgm) > 0:
            fgm = fgm[fgm['value']]
            fgm = fgm.rename(columns={'SHOT_METHOD': 'METHOD', 'variable': 'ATTRIBUTE', 'value': 'FGM'})
            fgm = fgm.groupby(['METHOD', 'ATTRIBUTE']).sum()
            
            shot_totals = pd.merge(fga, fgm, how = 'left', on=['METHOD', 'ATTRIBUTE']).fillna(0).astype(int).reset_index()
        else:
            shot_totals = fga.astype(int).reset_index()
            shot_totals['FGM'] = 0

        # Generate columns for the treemap (FG% = colour of node) and (% of method with attribute for size of the node)
        shot_totals['FG%'] = round(shot_totals['FGM']/shot_totals['FGA']*100,2)
        shot_totals = pd.merge(shot_totals, shots_grouped, left_on=['METHOD'], right_on=['SHOT_METHOD'])
        shot_totals['Pecentage of Method with Attribute'] = shot_totals['FGA']/shot_totals['SHOT_ATTEMPTED_FLAG']*100

        # Plot the Tree Map and the table showing the total number of shots for each method
        fig = px.treemap(shot_totals, path=['METHOD', 'ATTRIBUTE'], values='Pecentage of Method with Attribute',
                    color='FG%', hover_data=['FGA'],
                    color_continuous_scale='RdBu_r',
                    color_continuous_midpoint=50)
        fig.update_layout(width=900, height=700, margin=dict(l=0, r=0, t=0, b=0))

        col3.text('The tree map shot attribute node sizes are based on the % of shots taken with that attribute for that method. The size of the nodes for the actual shot method is not representative of anything only the layer inside each method is important.')
        col3.dataframe(shots_grouped)
        col4.plotly_chart(fig)
    
    # Display the table of the remaining shots after filtering
    st.markdown('---')
    st.dataframe(player_shots)
        
with tab2:
    # Using data source where player filtered is the second iD column select only the shots made - this will give all the assists the player had
    player_data2_shots = player_data2[player_data2['SHOT_MADE_FLAG'] == True]
    player_data2_shots = pd.merge(player_data2_shots, players, left_on='PLAYER1_ID', right_on='ID')

    # Filter to select which players that the fitlered player assisted in visuals
    ast_players = st.multiselect('Filter the Players Assisted for the below visuals', player_data2_shots['Name'].unique(), default=player_data2_shots['Name'].unique())
    player_data2_shots = player_data2_shots[player_data2_shots['Name'].isin(ast_players)]
    st.divider()

    col1, col2 = st.columns([0.2, 0.8])
   
    # Create Filter for each possible layer of the sankey visual
    sankey_layers = []
    ast_type = col1.checkbox('Shot Type (2PT or 3PT)]]', key='ast_type', value=True)
    if ast_type:
        sankey_layers.append('SHOT_TYPE')

    ast_zone = col1.checkbox('Shot Zone (Corner 3, Mid-Range, etc.)', key='ast_zone', value=True)
    if ast_zone:
        sankey_layers.append('SHOT_ZONE_BASIC')

    ast_method = col1.checkbox('Shot Method (Jump Shot, Layup Shot, etc.)', key='ast_method', value=True)
    if ast_method:
        sankey_layers.append('SHOT_METHOD')

    ast_player = col1.checkbox('Player Assisted', key='ast_player', value=True)
    if ast_player:
        sankey_layers.append('Name')

    # Create empty dataframe for the sankey
    player_ast_df = pd.DataFrame(columns=['source', 'target', 'value'])

    # Loop through select filter layers for the sankey and apend them to the empty datafrane in the same column format
    for col in sankey_layers:
        if len(player_ast_df) == 0:
            df = player_data2_shots.groupby([col])['GAME_ID'].count().reset_index()
            df = df.rename(columns={'GAME_ID': 'value', col: 'target'})
            df['source'] = player_name
            df = df[['source', 'target', 'value']]
        else:
            df = player_data2_shots.groupby([prev_col, col])['GAME_ID'].count().reset_index()
            df = df.rename(columns={'GAME_ID': 'value', col: 'target', prev_col: 'source'})
            df = df[['source', 'target', 'value']]

        player_ast_df = pd.concat([player_ast_df, df])
        prev_col = col

    # To plot sankey each label needs and assigned index value so create a list of all targets plus the player in index 0
    sankey_nodes = np.insert(player_ast_df['target'].unique(), 0, player_name)
    snakey_node_map = {}

    # Create a dictionary of the list and their index values to map to columns
    for index, name in enumerate(sankey_nodes):
        snakey_node_map[name] = index 
    
    # Create columns with index IDs to use in the sankey plot
    player_ast_df['target_node'] = player_ast_df['target'].map(snakey_node_map)
    player_ast_df['source_node'] = player_ast_df['source'].map(snakey_node_map)

    # Create Snakey plot
    fig = go.Figure(data=[go.Sankey(
    node = dict(
      pad = 15,
      thickness = 20,
      label = sankey_nodes
    ),
    link = dict(
      source = player_ast_df['source_node'],
      target = player_ast_df['target_node'],
      value = player_ast_df['value']
    ))])
    fig.update_layout(
    width=1200,
    height=800,
    title_text='Player Assists', font_size=15)
    col2.plotly_chart(fig)

    st.markdown('---')
    col3, col4 = st.columns([0.5, 0.5])    
    
    # Create Scatter plot for the location of all players assists
    plt.figure(figsize=(12,11))
    scatter_plot = plt.scatter(player_data2_shots['LOC_X'], player_data2_shots['LOC_Y'], s=50)
    draw_court(outer_lines=True)
    plt.xlim(-275, 275)
    plt.ylim(-75, 450)
    plt.axis('off')
    plt.title('Assist Locations')
    col3.pyplot(plt)
    
    # Get dataframe of all the players turnovers
    player1_tov = player_data1[player_data1['EVENTMSGTYPE'] == 5]
    player1_tov = player1_tov.drop_duplicates()

    player1_tov['TURNOVER_TYPE'] = ''
    player1_tov['DESCRIPTION'] = player1_tov['DESCRIPTION'].str.upper()

    # List of all turnover types
    turnover_types = ['LOST BALL TURNOVER', 'BACKCOURT TURNOVER', 'FOUL TURNOVER', 'DRIBBLE TURNOVER', 'KICKED BALL VIOLATION TURNOVER', 'BAD PASS TURNOVER', 'LANE VIOLATION TURNOVER', 'TRAVELING TURNOVER', 'STEP OUT OF BOUNDS TURNOVER', 'PALMING TURNOVER']

    # Fill in turnover type column based on string contains
    for tov in turnover_types:
        player1_tov['TURNOVER_TYPE'] = np.where(player1_tov['DESCRIPTION'].str.contains(tov), tov, player1_tov['TURNOVER_TYPE'])

    player1_tov = player1_tov[player1_tov['TURNOVER_TYPE'] != '']
    player1_tov = player1_tov.groupby('TURNOVER_TYPE')['PLAYER1_ID'].count().reset_index().sort_values('PLAYER1_ID', ascending=True)

    # Plot Count of each turnover type in bar chart
    plt.figure(figsize=(12,11))
    plt.barh(player1_tov['TURNOVER_TYPE'], player1_tov['PLAYER1_ID'])
    plt.title('Turnover Types')
    col4.pyplot(plt)

# %%