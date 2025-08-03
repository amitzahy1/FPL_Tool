import json

# Read data from the FPL JSON file
with open('FPL_Bootstrap_static.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Team and position mappings
teams = {team['id']: team['name'] for team in data['teams']}
positions = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}

# --- Normalization and Position-Specific Draft Score ---
def normalize_stat(value, max_value, reverse=False):
    if max_value == 0: return 0
    score = value / max_value
    return (1 - score) if reverse else score

def calculate_draft_score(player, all_players_elements):
    pos = player.get('element_type')
    
    max_stats = {
        'saves': max((p.get('saves', 0) for p in all_players_elements if p.get('element_type') == 1), default=1),
        'clean_sheets': max((p.get('clean_sheets', 0) for p in all_players_elements), default=1),
        'bps': max((p.get('bps', 0) for p in all_players_elements), default=1),
        'ppg': max((float(p.get('points_per_game', 0)) for p in all_players_elements), default=1),
        'bonus': max((p.get('bonus', 0) for p in all_players_elements), default=1),
        'ict_index': max((float(p.get('ict_index', 0)) for p in all_players_elements), default=1),
        'xg': max((float(p.get('expected_goals', 0)) for p in all_players_elements), default=1),
        'xa': max((float(p.get('expected_assists', 0)) for p in all_players_elements), default=1),
        'xGC': max((float(p.get('expected_goals_conceded', 0)) for p in all_players_elements), default=1),
    }

    score = 0
    minutes = player.get('minutes', 0)
    if minutes == 0:
        price_score = normalize_stat(player.get('now_cost', 0), 130) * 0.7
        ict_score = normalize_stat(float(player.get('ict_index', 0)), max_stats['ict_index']) * 0.3
        return round((price_score + ict_score) * 50)

    if pos == 1: # GKP
        saves_score = normalize_stat(player.get('saves', 0), max_stats['saves']) * 0.30
        cs_score = normalize_stat(player.get('clean_sheets', 0), max_stats['clean_sheets']) * 0.25
        bps_score = normalize_stat(player.get('bps', 0), max_stats['bps']) * 0.15
        ppg_score = normalize_stat(float(player.get('points_per_game', 0)), max_stats['ppg']) * 0.10
        bonus_score = normalize_stat(player.get('bonus', 0), max_stats['bonus']) * 0.05
        xGC_val = float(player.get('expected_goals_conceded', 0))
        actual_gc = player.get('goals_conceded', 0)
        xGC_diff_score = normalize_stat(xGC_val - actual_gc, max((float(p.get('expected_goals_conceded', 0)) - p.get('goals_conceded', 0) for p in all_players_elements), default=1)) * 0.15
        score = (saves_score + cs_score + bps_score + ppg_score + bonus_score + xGC_diff_score)
        
    elif pos == 2: # DEF
        ict_score = normalize_stat(float(player.get('ict_index', 0)), max_stats['ict_index']) * 0.20
        cs_score = normalize_stat(player.get('clean_sheets', 0), max_stats['clean_sheets']) * 0.40
        xga_score = normalize_stat(float(player.get('expected_goals', 0)) + float(player.get('expected_assists', 0)), max_stats['xg'] + max_stats['xa']) * 0.30
        bps_score = normalize_stat(player.get('bps', 0), max_stats['bps']) * 0.10
        bonus_score = 0 # Explicitly set to 0 as per user request
        score = (ict_score + cs_score + xga_score + bps_score + bonus_score)

    elif pos == 3: # MID
        ict_score = normalize_stat(float(player.get('ict_index', 0)), max_stats['ict_index']) * 0.10
        xga_score = normalize_stat(float(player.get('expected_goals', 0)) + float(player.get('expected_assists', 0)), max_stats['xg'] + max_stats['xa']) * 0.40
        bps_score = normalize_stat(player.get('bps', 0), max_stats['bps']) * 0.15
        ppg_score = normalize_stat(float(player.get('points_per_game', 0)), max_stats['ppg']) * 0.25
        bonus_score = normalize_stat(player.get('bonus', 0), max_stats['bonus']) * 0.10
        score = (ict_score + xga_score + bps_score + ppg_score + bonus_score)
        
    elif pos == 4: # FWD
        xg_score = normalize_stat(float(player.get('expected_goals', 0)), max_stats['xg']) * 0.30
        ict_score = normalize_stat(float(player.get('ict_index', 0)), max_stats['ict_index']) * 0.15
        bps_score = normalize_stat(player.get('bps', 0), max_stats['bps']) * 0.15
        ppg_score = normalize_stat(float(player.get('points_per_game', 0)), max_stats['ppg']) * 0.40
        score = (xg_score + ict_score + bps_score + ppg_score)

    return round(score * 100)

# --- Main Data Processing Loop ---
processed_players = []
all_players_elements = data['elements']
for player in all_players_elements:
    draft_score = calculate_draft_score(player, all_players_elements)

    processed_players.append({
        'id': player['id'],
        'name': f"{player.get('first_name', '')} {player.get('web_name', '')}",
        'team': teams.get(player['team'], 'Unknown'),
        'position': positions.get(player['element_type'], 'N/A'),
        'price': player.get('now_cost', 0) / 10,
        'total_points': player.get('total_points', 0),
        'ppg': float(player.get('points_per_game', 0)),
        'selected_percent': float(player.get('selected_by_percent', 0)),
        'goals': player.get('goals_scored', 0),
        'assists': player.get('assists', 0),
        'minutes': player.get('minutes', 0),
        'xg': float(player.get('expected_goals', 0)),
        'xa': float(player.get('expected_assists', 0)),
        'bps': player.get('bps', 0),
        'ict_index': float(player.get('ict_index', 0)),
        'bonus': player.get('bonus', 0),
        'clean_sheets': player.get('clean_sheets', 0),
        'draft_score': draft_score,
        'penalty_taker': player.get('penalties_order', 0) in [1, 2],
        'corners_taker': player.get('corners_and_indirect_freekicks_order') in [1, 2],
        'rotation_risk': player.get('minutes', 0) < 1500 and (player.get('now_cost', 0) / 10) > 5.0
    })

# --- HTML Generation ---
def generate_html(players):
    players_json = json.dumps(players)

    html_template = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FPL Ultimate Draft Tool</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh; padding: 15px; line-height: 1.4; max-width: 1400px; margin: 0 auto;
        }}
        .header {{ text-align: center; margin-bottom: 20px; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; font-size: 1.8em; margin-bottom: 8px; font-weight: 700; }}
        .subtitle {{ color: #7f8c8d; font-size: 1em; font-weight: 500; }}
        .legend {{
            background: #fff; padding: 12px; border-radius: 8px; text-align: center;
            margin-bottom: 20px; font-size: 0.9em; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }}
        .legend-item {{ display: inline-block; margin: 0 10px; }}
        .legend-title {{ font-weight: 600; cursor: help; border-bottom: 1px dotted #2c3e50; }}
        .filters {{ background: white; padding: 15px; margin-bottom: 15px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.1); display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; align-items: end; }}
        .filter-group {{ display: flex; flex-direction: column; }}
        label {{ font-weight: 600; margin-bottom: 4px; color: #2c3e50; font-size: 0.85em; }}
        select, input {{ padding: 8px; border: 2px solid #ecf0f1; border-radius: 6px; font-size: 12px; transition: all 0.3s ease; }}
        select:focus, input:focus {{ outline: none; border-color: #a1c4fd; box-shadow: 0 0 0 3px rgba(161, 196, 253, 0.2); }}
        .controls {{ display: flex; gap: 10px; margin-bottom: 15px; justify-content: center; flex-wrap: wrap; }}
        .control-button {{
            background: linear-gradient(135deg, #e2e8f0 0%, #f1f5f9 100%); color: #475569;
            border: 1px solid #cbd5e1; padding: 8px 16px; border-radius: 8px; cursor: pointer;
            font-weight: 600; transition: all 0.3s ease; font-size: 0.85em;
        }}
        .control-button:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); }}
        .control-button.active {{ background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); color: #333; border-color: #a1c4fd; }}
        .table-container {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 6px 20px rgba(0,0,0,0.1); overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.8em; }}
        th {{ background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); color: #333; padding: 10px 6px; text-align: center; font-weight: 600; white-space: nowrap; cursor: pointer; user-select: none; transition: all 0.3s ease; position: sticky; top: 0; z-index: 10; font-size: 0.75em; }}
        th:hover {{ background: linear-gradient(135deg, #8ab2f2 0%, #a1c4fd 100%); }}
        th.sorted {{ background: linear-gradient(135deg, #8ab2f2 0%, #a1c4fd 100%); }}
        td {{ padding: 8px 6px; border-bottom: 1px solid #f8f9fa; white-space: nowrap; font-size: 0.8em; text-align: center; }}
        tr:hover {{ background: #f1f5f9; }}
        .name-cell {{ font-weight: 600; color: #2c3e50; min-width: 100px; text-align:right; }}
        .player-name-icon {{ margin-right: 5px; font-size: 0.9em; }}
        .verbal-insights-cell {{ white-space: normal; font-size: 0.75em; line-height: 1.2; color: #5a6c7d; min-width: 150px; text-align: right;}}
        .position-gkp {{ background-color: #fff3cd !important; }}
        .position-def {{ background-color: #d1ecf1 !important; }}
        .position-mid {{ background-color: #d4edda !important; }}
        .position-fwd {{ background-color: #f8d7da !important; }}
        .xdiff-positive {{ color: #27ae60; font-weight: 600; }}
        .xdiff-negative {{ color: #e74c3c; font-weight: 600; }}
        .sort-indicator {{ display: inline-block; margin-left: 3px; }}
        .modal {{
            display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%;
            overflow: auto; background-color: rgba(0,0,0,0.4);
        }}
        .modal-content {{
            background-color: #fefefe; margin: 5% auto; padding: 20px; border: 1px solid #888;
            width: 90%; max-width: 1200px; border-radius: 12px;
        }}
        .close {{ color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }}
        #compareTable th {{ background: linear-gradient(135deg, #c2e9fb 0%, #a1c4fd 100%); }}
        #compareTable {{ width: auto; margin: 0 auto; border-collapse: separate; border-spacing: 0; }}
        #compareTable th, #compareTable td {{ border: 1px solid #ddd; padding: 8px; }}
        #compareTable td {{ font-size: 1.1em; }}
        .value-best {{ background-color: #d4edda; }}
        .value-good {{ background-color: #e2f0d9; }}
        .value-mid {{ background-color: #fff2cc; }}
        .value-bad {{ background-color: #f8d7da; }}
        .value-worst {{ background-color: #f5c6cb; }}
    </style>
</head>
<body>
    <div class="container">
    <div class="header">
            <h1>🏆 FPL Ultimate Draft Tool</h1>
            <p class="subtitle">ניתוח חכם | ציון דראפט ייעודי | סינון מתקדם</p>
        </div>
        <div class="legend">
            <p>
                <span class="legend-item"><strong class="legend-title" title="ציון ייעודי המחושב לפי עמדה להערכת שווי בדראפט. מבוסס על מדדים כמו xG, xA, ICT, BPS, שערים נקיים ועוד, עם משקולות שונות לכל עמדה.">ציון דראפט</strong></span>
                <span class="legend-item"><strong class="legend-title" title="ההפרש בין שערים ובישולים בפועל (G+A) לביצוע הצפוי (xG+xA). ערך חיובי (ירוק) = ביצועי יתר (מעל המצופה). ערך שלילי (אדום) = ביצועי חסר (מתחת למצופה).">xDiff</strong></span>
                <span class="legend-item"><strong class="legend-title" title="מדד השפעה, יצירתיות ואיום">ICT</strong></span>
            </p>
    </div>
    <div class="filters">
            <div class="filter-group"><label>🔍 חיפוש שחקן:</label><input type="text" id="searchName" onkeyup="processChange()" placeholder="שם שחקן..."></div>
            <div class="filter-group"><label>⚽ עמדה:</label><select id="positionFilter" onchange="processChange()"><option value="">כל העמדות</option><option value="GKP">🥅 שוערים</option><option value="DEF">🛡️ מגנים</option><option value="MID">⚽ קשרים</option><option value="FWD">🎯 חלוצים</option></select></div>
            <div class="filter-group"><label>🏟️ קבוצה:</label><select id="teamFilter" onchange="processChange()"><option value="">כל הקבוצות</option></select></div>
            <div class="filter-group"><label>💰 מחיר טווח:</label><input type="text" id="priceRange" onkeyup="processChange()" placeholder="4.0-15.0"></div>
            <div class="filter-group"><label>🏆 נקודות מינימום:</label><input type="number" id="minPoints" onkeyup="processChange()" placeholder="0"></div>
            <div class="filter-group"><label>📊 % בחירה מינימלי:</label><input type="number" id="minSelected" step="0.0001" onkeyup="processChange()" placeholder="0.0001" value="0.0001"></div>
            <div class="filter-group"><label>🎯 טווח xDiff:</label><select id="xDiffFilter" onchange="processChange()"><option value="">כל הטווח</option><option value="positive">חיובי (ביצועי יתר)</option><option value="negative">שלילי (ביצועי חסר)</option></select></div>
            <div class="filter-group"><label>הצג:</label><select id="showEntries" onchange="processChange()"><option value="50">50</option><option value="100">100</option><option value="200">200</option><option value="all" selected>הכל</option></select></div>
        </div>
    <div class="controls">
            <button class="control-button active" onclick="showAllPlayers(this)">כל השחקנים</button>
            <button class="control-button" id="compareBtn" onclick="compareSelectedPlayers()">השווה שחקנים נבחרים</button>
            <button class="control-button" data-filter-name="differentials" onclick="quickFilter(this, 'differentials')">💎 Differentials</button>
            <button class="control-button" data-filter-name="penalties" onclick="quickFilter(this, 'penalties')">🎯 בועטי פנדלים</button>
            <button class="control-button" data-filter-name="corners" onclick="quickFilter(this, 'corners')">⚽ מרימי קרנות</button>
            <button class="control-button" data-filter-name="clean_sheets" onclick="quickFilter(this, 'clean_sheets')">🥅 שער נקי</button>
            <button class="control-button" data-filter-name="underperforming" onclick="quickFilter(this, 'underperforming')">📉 ביצועי חסר</button>
            <button class="control-button" data-filter-name="overperforming" onclick="quickFilter(this, 'overperforming')">📈 ביצועי יתר</button>
            <button class="control-button" data-filter-name="bonus_magnets" onclick="quickFilter(this, 'bonus_magnets')">🎖️ מגנטי בונוס</button>
            <button class="control-button" data-filter-name="value" onclick="quickFilter(this, 'value')">💰 ערך מצוין</button>
        <button class="control-button" onclick="exportToCsv()">📁 יצוא CSV</button>
    </div>
    <div class="table-container">
        <table id="playersTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">דירוג<span class="sort-indicator"></span></th>
                    <th onclick="sortTable(1)">שחקן<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(2)">ציון דראפט<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(3)">קבוצה<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(4)">עמדה<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(5)">מחיר<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(6)">נקודות<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(7)">נק/משחק<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(8)">בחירה %<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(9)">ש+ב<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(10)">xG+xA<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(11)">דקות<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(12)">xDiff<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(13)">BPS<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(14)">ICT<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(15)">בונוס<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(16)">שער נקי<span class="sort-indicator"></span></th>
                        <th onclick="sortTable(17)">תובנות<span class="sort-indicator"></span></th>
                        <th>בחר</th>
                </tr>
            </thead>
            <tbody id="playersTableBody"></tbody>
        </table>
    </div>

    <div id="compareModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>השוואת שחקנים</h2>
            <div class="table-container">
                <table id="compareTable"></table>
            </div>
        </div>
    </div>

    </div>
    <script>
        const allPlayers = {players_json};
        let displayedData = [];
        let sortColumn = 2;
        let sortDirection = 'desc';
        let activeQuickFilterName = null;

        const quickFilterFunctions = {{
            'differentials': p => p.selected_percent < 5 && p.total_points > 30,
            'penalties': p => p.penalty_taker,
            'corners': p => p.corners_taker,
            'underperforming': p => parseFloat(calculateXDiff(p)) <= -4,
            'overperforming': p => parseFloat(calculateXDiff(p)) >= 4,
            'bonus_magnets': p => p.bps > 20,
            'value': p => (p.price > 0 && (p.ppg / p.price) > 0.8 && p.total_points > 50),
            'clean_sheets': p => p.clean_sheets > 8
        }};

        const calculateXDiff = p => ((p.goals + p.assists) - (p.xg + p.xa)).toFixed(2);

        function generatePlayerIcons(p) {{
            const icons = [];
            if (p.penalty_taker) icons.push(`<span class='player-name-icon'>🎯</span>`);
            if (p.corners_taker) icons.push(`<span class='player-name-icon'>⚽</span>`);
            if (p.selected_percent < 5) icons.push(`<span class='player-name-icon'>💎</span>`);
            if (p.rotation_risk) icons.push(`<span class='player-name-icon'>⚠️</span>`);
            if (parseFloat(calculateXDiff(p)) > 1) icons.push(`<span class='player-name-icon'>📈</span>`); // Overperforming
            if (parseFloat(calculateXDiff(p)) < -1) icons.push(`<span class='player-name-icon'>📉</span>`); // Underperforming
            if (p.price > 0 && (p.ppg / p.price) > 0.8 && p.total_points > 50) icons.push(`<span class='player-name-icon'>💰</span>`);
            if (p.bps > 500) icons.push(`<span class='player-name-icon'>🎖️</span>`);
            return icons.join("");
        }}

        function generateVerbalInsights(p) {{
            const insights = [];
            if (p.penalty_taker) insights.push("בועט פנדלים");
            if (p.corners_taker) insights.push("לוקח קרנות");
            if (p.selected_percent < 5) insights.push("דיפרנציאל");
            if (p.rotation_risk) insights.push("סיכון רוטציה");
            if (parseFloat(calculateXDiff(p)) > 1) insights.push("במימוש יתר");
            if (parseFloat(calculateXDiff(p)) < -1) insights.push("בביצועי חסר, צפוי להשתפר");
            if (p.price > 0 && (p.ppg / p.price) > 0.8 && p.total_points > 50) insights.push("תמורה מעולה למחיר");
            if (p.bps > 500) insights.push("מגנט בונוסים");
            return insights.join(', ');
        }}
        
        function populateTeamFilter() {{
            const teamFilter = document.getElementById('teamFilter');
            const uniqueTeams = [...new Set(allPlayers.map(p => p.team))].sort();
            uniqueTeams.forEach(team => teamFilter.add(new Option(team, team)));
        }}
        
        function renderTable() {{
            const tbody = document.getElementById('playersTableBody');
            const showCount = document.getElementById('showEntries').value;
            const dataToRender = showCount === 'all' ? displayedData : displayedData.slice(0, parseInt(showCount));
            tbody.innerHTML = '';
            
            dataToRender.forEach((p, index) => {{
                const row = tbody.insertRow();
                row.className = `position-${{p.position.toLowerCase()}}`;
                const xDiff = calculateXDiff(p);
                let xDiffClass = '';
                if (parseFloat(xDiff) > 0) xDiffClass = 'xdiff-positive';
                else if (parseFloat(xDiff) < 0) xDiffClass = 'xdiff-negative';

                row.innerHTML = `
                    <td>${{index + 1}}</td>
                    <td class="name-cell">${{generatePlayerIcons(p)}}${{p.name}}</td>
                    <td><b>${{p.draft_score}}</b></td>
                    <td>${{p.team}}</td>
                    <td><b>${{p.position}}</b></td>
                    <td><b>£${{p.price.toFixed(1)}}</b></td>
                    <td><b>${{p.total_points}}</b></td>
                    <td>${{p.ppg.toFixed(1)}}</td>
                    <td>${{p.selected_percent.toFixed(1)}}%</td>
                    <td><b>${{p.goals + p.assists}}</b></td>
                    <td><b>${{(p.xg + p.xa).toFixed(2)}}</b></td>
                    <td>${{p.minutes}}</td>
                    <td class="${{xDiffClass}}"><b>${{xDiff}}</b></td>
                    <td>${{p.bps}}</td>
                    <td>${{p.ict_index.toFixed(1)}}</td>
                    <td>${{p.bonus}}</td>
                    <td>${{p.clean_sheets}}</td>
                    <td class="verbal-insights-cell">${{generateVerbalInsights(p)}}</td>
                    <td><input type="checkbox" class="compare-checkbox" data-player-id="${{p.id}}"></td>
                `;
            }});
        }}
        
        function processChange() {{
            const searchName = document.getElementById('searchName').value.toLowerCase();
            const position = document.getElementById('positionFilter').value;
            const team = document.getElementById('teamFilter').value;
            const priceRange = document.getElementById('priceRange').value;
            const minPoints = parseInt(document.getElementById('minPoints').value, 10) || 0;
            const minSelected = parseFloat(document.getElementById('minSelected').value) || 0;
            const xDiffFilter = document.getElementById('xDiffFilter').value;
            
            let [minPrice, maxPrice] = [0, 99];
            if (priceRange && priceRange.includes('-')) {{
                [minPrice, maxPrice] = priceRange.split('-').map(p => parseFloat(p.trim())).filter(v => !isNaN(v));
                if (typeof maxPrice === 'undefined') maxPrice = 99;
            }}
            
            let filtered = allPlayers.filter(p => {{
                const xDiff = parseFloat(calculateXDiff(p));
                const xDiffMatch = !xDiffFilter || (xDiffFilter === 'positive' && xDiff > 0) || (xDiffFilter === 'negative' && xDiff < 0);
                return p.name.toLowerCase().includes(searchName) && (!position || p.position === position) && (!team || p.team === team) && p.price >= (minPrice || 0) && p.price <= (maxPrice || 99) && p.total_points >= minPoints && p.selected_percent >= minSelected && xDiffMatch;
            }});
            
            if (activeQuickFilterName && quickFilterFunctions[activeQuickFilterName]) {{
                filtered = filtered.filter(quickFilterFunctions[activeQuickFilterName]);
            }}

            sortAndDisplay(filtered);
        }}

        function sortAndDisplay(data) {{
            const fields = ['rank', 'name', 'draft_score', 'team', 'position', 'price', 'total_points', 'ppg', 'selected_percent', 'goals_assists', 'xg_xa', 'minutes', 'xDiff', 'bps', 'ict_index', 'bonus', 'clean_sheets', 'verbal_insights'];
            const sortField = fields[sortColumn];
            
            data.sort((a, b) => {{
                let valA, valB;

                if (sortField === 'goals_assists') {{ valA = a.goals + a.assists; valB = b.goals + b.assists; }}
                else if (sortField === 'xg_xa') {{ valA = a.xg + a.xa; valB = b.xg + b.xa; }}
                else if (sortField === 'xDiff') {{ valA = parseFloat(calculateXDiff(a)); valB = parseFloat(calculateXDiff(b)); }}
                else if (sortField === 'verbal_insights') {{ valA = generateVerbalInsights(a); valB = generateVerbalInsights(b); }}
                else {{ valA = a[sortField]; valB = b[sortField]; }}

                if (typeof valA === 'string') {{
                    // For string comparison, we'll let the user decide on ascending/descending later if needed
                    return valA.localeCompare(valB, 'he');
                }}
                
                // For numbers, always sort descending
                return (valB || 0) - (valA || 0);
            }});

            displayedData = data;
            renderTable();
        }}

        function sortTable(columnIndex) {{
            sortColumn = columnIndex;
            processChange();
            
            document.querySelectorAll('th').forEach((th, i) => {{
                th.classList.remove('sorted');
                const indicator = th.querySelector('.sort-indicator');
                indicator.textContent = '';
                if (i === columnIndex) {{
                    th.classList.add('sorted');
                    indicator.textContent = '▼'; 
                }}
            }});
        }}

        function setActiveButton(button) {{
            document.querySelectorAll('.control-button').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
        }}

        function showAllPlayers(btn) {{
            setActiveButton(btn);
            activeQuickFilterName = null;
            document.querySelectorAll('.filters input, .filters select').forEach(el => {{
                if (el.id !== 'showEntries' && el.id !== 'minSelected') el.value = '';
            }});
            document.getElementById('minSelected').value = '0.0001';
            processChange();
        }}
        
        function quickFilter(btn, filterName) {{
            const wasActive = btn.classList.contains('active');
            
            document.querySelectorAll('.control-button').forEach(b => b.classList.remove('active'));

            if (wasActive) {{
                activeQuickFilterName = null;
                document.querySelector('.control-button[onclick^="showAllPlayers"]').classList.add('active');
            }} else {{
                activeQuickFilterName = filterName;
                btn.classList.add('active');
            }}
            processChange();
        }}

        function exportToCsv() {{
            const headers = ['Rank','Player','Draft Score','Team','Position','Price','Points','PPG','Selected %','G+A','xG+xA','Minutes','xDiff','BPS','ICT','Bonus','Clean Sheets','Insights'];
            let csvContent = headers.join(',') + '\\n';
            displayedData.forEach((p, i) => {{
                const row = [i + 1, p.name.replace(/,/g, ''), p.draft_score, p.team, p.position, p.price, p.total_points, p.ppg, p.selected_percent, p.goals + p.assists, (p.xg + p.xa).toFixed(2), p.minutes, calculateXDiff(p), p.bps, p.ict_index, p.bonus, p.clean_sheets, `"${{generateVerbalInsights(p)}}"`];
                csvContent += row.join(',') + '\\n';
            }});
            const blob = new Blob([`\uFEFF${{csvContent}}`], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement("a");
            link.setAttribute("href", URL.createObjectURL(blob));
            link.setAttribute("download", "fpl_draft_data.csv");
            link.click();
        }}
        
        function compareSelectedPlayers() {{
            const selectedIds = [...document.querySelectorAll('.compare-checkbox:checked')].map(cb => parseInt(cb.dataset.playerId));
            if (selectedIds.length < 2) {{
                alert('יש לבחור לפחות שני שחקנים להשוואה.');
                return;
            }}
            const playersToCompare = allPlayers.filter(p => selectedIds.includes(p.id));

            const modal = document.getElementById('compareModal');
            const table = document.getElementById('compareTable');
            table.innerHTML = ''; // Clear previous comparison

            if (playersToCompare.length > 0) {{
                const headers = ['Metric', ...playersToCompare.map(p => p.name)];
                let headerHtml = '<thead><tr>';
                headers.forEach(h => headerHtml += `<th>${{h}}</th>`);
                headerHtml += '</tr></thead>';
                table.innerHTML = headerHtml;

                const metrics = [
                    {{key: 'position', label: 'עמדה', type: 'string'}},
                    {{key: 'draft_score', label: 'ציון דראפט', type: 'number'}},
                    {{key: 'price', label: 'מחיר', type: 'number', reverse: true}},
                    {{key: 'total_points', label: 'סה"כ נקודות', type: 'number'}},
                    {{key: 'ppg', label: 'נק/משחק', type: 'number'}},
                    {{key: 'goals_assists', label: 'שערים+בישולים', type: 'number'}},
                    {{key: 'xg_xa', label: 'xG+xA', type: 'number'}},
                    {{key: 'xDiff', label: 'xDiff', type: 'number'}},
                    {{key: 'clean_sheets', label: 'שער נקי', type: 'number'}},
                    {{key: 'bps', label: 'BPS', type: 'number'}},
                    {{key: 'ict_index', label: 'ICT', type: 'number'}},
                    {{key: 'penalty_taker', label: 'בועט פנדלים', type: 'boolean'}},
                    {{key: 'corners_taker', label: 'מרים קרנות', type: 'boolean'}},
                    {{key: 'minutes', label: 'דקות', type: 'number'}},
                ];

                let bodyHtml = '<tbody>';

                // Pre-calculate combined values
                playersToCompare.forEach(p => {{
                    p.goals_assists = p.goals + p.assists;
                    p.xg_xa = p.xg + p.xa;
                    p.xDiff = parseFloat(calculateXDiff(p));
                }});

                metrics.forEach(metric => {{
                    bodyHtml += `<tr><td><strong>${{metric.label}}</strong></td>`;

                    if (metric.type === 'string') {{
                        playersToCompare.forEach(p => {{
                            bodyHtml += `<td>${{p[metric.key]}}</td>`;
                        }});
                    }} else if (metric.type === 'boolean') {{
                         playersToCompare.forEach(p => {{
                            const displayValue = p[metric.key] ? 'כן' : 'לא';
                            const colorClass = p[metric.key] ? 'value-best' : '';
                            bodyHtml += `<td class="${{colorClass}}">${{displayValue}}</td>`;
                        }});
                    }} else {{
                        const metricValues = playersToCompare.map(p => p[metric.key]).filter(v => typeof v === 'number');
                        const min = Math.min(...metricValues);
                        const max = Math.max(...metricValues);

                        playersToCompare.forEach(p => {{
                            const value = p[metric.key];
                            let displayValue = value;
                            if (typeof value === 'number' && !Number.isInteger(value)) {{
                               displayValue = value.toFixed(2);
                            }}
                            
                            const colorClass = getColorClass(value, min, max, !!metric.reverse);
                            bodyHtml += `<td class="${{colorClass}}">${{displayValue}}</td>`;
                        }});
                    }}
                    bodyHtml += '</tr>';
                }});
                bodyHtml += '</tbody>';
                table.innerHTML += bodyHtml;

                modal.style.display = 'block';
            }}
        }}

        function getColorClass(value, min, max, reverse = false) {{
            if (typeof value !== 'number' || min === max) return '';
            
            const range = max - min;
            const normalized = (value - min) / range;
            
            const effectiveNormalized = reverse ? 1 - normalized : normalized;

            if (effectiveNormalized > 0.95) return 'value-best';
            if (effectiveNormalized > 0.65) return 'value-good';
            if (effectiveNormalized > 0.35) return 'value-mid';
            if (effectiveNormalized > 0.05) return 'value-bad';
            return 'value-worst';
        }}

        function closeModal() {{
            document.getElementById('compareModal').style.display = 'none';
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            populateTeamFilter();
            sortTable(2); // Initial sort by draft score, descending
        }});
    </script>
</body>
</html>
    """
    return html_template.format(players_json=players_json)


if __name__ == "__main__":
    html_content = generate_html(processed_players)
    output_filename = 'FPL_Ultimate_Draft_Tool.html'
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Successfully generated {output_filename} with {len(processed_players)} players.") 