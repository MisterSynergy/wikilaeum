<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="author" content="MisterSynergy">
<meta http-equiv="reply-to" content="mister.synergy@yahoo.com">
<meta name="description" content="Wikiläum-Tool von MisterSynergy">
<meta name="keywords" lang="de" content="Wikiläum, deutschsprachige Wikipedia, Wikipedia, dewiki">
<meta name="robots" content="noindex, nofollow">
<title>Wikipedia:Wikiläum der deutschsprachigen Wikipedia</title>
<link href="./favicon.ico" rel="shortcut icon" type="image/x-icon">
<link href="./style.css" rel="stylesheet" type="text/css">
</head>
<body>
<header>
<h1><a href="https://de.wikipedia.org/wiki/Wikipedia:Wikiläum" title="Wikiläum-Seite in der deutschsprachigen Wikipedia">[[Wikipedia:Wikiläum]]</a></h1>
</header>
<?php

// basic setup
include_once('./Database.php');

$tooluser = posix_getpwuid(posix_getuid());
if(false === ($config = parse_ini_file($tooluser['dir'] . '/wikilaeum/config.ini', TRUE))){
	exit('cannot read global configuration');
}

// input parameters
$wikilaeums = array(5 => "Bronze", 10 => "Silber", 15 => "Rubin", 20 => "Gold", 30 => "Platin", 40 => "Diamant", 50 => "Eisen"); // per https://de.wikipedia.org/wiki/Wikipedia:Wikil%C3%A4um

$footer_html  = '<p>' . "\n";
$footer_html .= 'Ein Tool von <a href="https://de.wikipedia.org/wiki/User:MisterSynergy" title=":de:User:MisterSynergy">MisterSynergy</a>' . "\n";
$footer_html .= ' • <a href="https://wikitech.wikimedia.org/wiki/Tool:Wikilaeum" title="Infoseite im wikitech-wiki">Infoseite</a> im <a href="https://wikitech.wikimedia.org/" title="Wikitech-Wiki">wikitech-wiki</a>' . "\n";
$footer_html .= ' • <a href="https://github.com/MisterSynergy/wikilaeum" title="Quellcode">Quellcode bei github.com</a>' . "\n";
$daily_update_log = file_get_contents($tooluser['dir'] . '/daily_update_log.txt');
$footer_html .= '<!-- ' . $daily_update_log . ' -->' . "\n";
$commit_version = file_get_contents($tooluser['dir'] . '/commit_version_and_timestamp.txt');
$footer_html .= '<!-- ' . str_replace("\n", ", ", $commit_version) . ' -->' . "\n";
$footer_html .= '</p>';

unset($tooluser);

// define some useful variables
$years = range(2006, 2026);
$months = array(1 => "Januar", 2 => "Februar", 3 => "März", 4 => "April", 5 => "Mai", 6 => "Juni", 7 => "Juli", 8 => "August", 9 => "September", 10 => "Oktober", 11 => "November", 12 => "Dezember");
$days = range(1, 31);
date_default_timezone_set($config['timezone']);

// read parameters
$year = isset($_GET['year'])?intval($_GET['year']):null;
$month = isset($_GET['month'])?intval($_GET['month']):null;
$day = isset($_GET['day'])?intval($_GET['day']):null;
$min_editcount = isset($_GET['min_editcount'])?intval($_GET['min_editcount']):intval($config['editcount_default']);

// verify input
$invalid_date = false;
if((true === in_array($month, array(4, 6, 9, 11)) && $day === 31) || ($month === 2 && intval(bcmod($year, 4)) !== 0 && $day > 28) || ($month === 2 && intval(bcmod($year, 4)) === 0 && $day > 29)){
	$invalid_date = true;
	$day = 1;
}
if($year === null && $month === null && $day === null){ // if no input is given, select todays date
	$invalid_date = true; // but do not evaluate result yet
	$year = intval(date('Y', time()));
	$month = intval(date('n', time()));
	$day = intval(date('j', time()));
}
if(false === in_array($year, $years, true) || false === in_array($month, array_keys($months), true) || false === in_array($day, $days, true)){
	$invalid_date = true;
}

if(false === $invalid_date){
	$timestmp = mktime(12, 0, 0, $month, $day, $year);
	$timestmpMinusOneDay = $timestmp - 86400;
	$timestmpPlusOneDay = $timestmp + 86400;
}


// print input form
echo '<nav>' . "\n";
echo '<form action="' . $_SERVER['SCRIPT_NAME'] . '" method="GET">' . "\n";
if(isset($_GET['min_editcount']) && intval($_GET['min_editcount'])<intval($config['editcount_threshold'])){
	$min_editcount = intval($config['editcount_threshold']);
	echo '<p>Benutzer mit Beitragszahlen unter ' . $config['editcount_threshold'] . ' können nicht ausgewertet werden.</p>' . "\n";
}
echo '<label>Datum</label>: <label for="day" class="noshow">Tag</label><select name="day" id="day">';
foreach($days as $d){
	echo '<option value="' . $d . '"' . ($d===$day?' selected="selected"':'') . '>' . $d . '</option>';
}
echo '</select>' . "\n";
echo '<label for="month" class="noshow">Monat</label><select name="month" id="month">';
foreach($months as $m => $mname){
	echo '<option value="' . $m . '"' . ($m===$month?' selected="selected"':'') . '>' . $mname . '</option>';
}
echo '</select>' . "\n";
echo '<label for="year" class="noshow">Jahr</label><select name="year" id="year">';
foreach($years as $y){
	echo '<option value="' . $y . '"' . ($y===$year?' selected="selected"':'') . '>' . $y . '</option>';
}
echo '</select>' . "\n";
echo '<span class="separator">•</span>' . "\n";
echo '<label for="min_editcount">Mindestbeitragszahl</label>: <input type="text" name="min_editcount" id="min_editcount" value="' . $min_editcount . '">' . "\n";
echo '<span class="separator">•</span>' . "\n";
echo '<input type="submit" value="auswerten">' . "\n";
if(isset($timestmpMinusOneDay)){
	echo '<span class="separator">•</span>' . "\n";
	echo '<a href="' . $_SERVER['SCRIPT_NAME'] . '?day=' . date('j', $timestmpMinusOneDay) . '&amp;month=' . date('n', $timestmpMinusOneDay) . '&amp;year=' . date('Y', $timestmpMinusOneDay) . '&amp;min_editcount=' . $min_editcount . '" title="Auswertung des Vortages (' . date('j', $timestmpMinusOneDay) . '. ' . $months[intval(date('n', $timestmpMinusOneDay))] . ' ' . date('Y', $timestmpMinusOneDay) . ')">Vortag</a>' . "\n";
}
if(isset($timestmpPlusOneDay)){
	echo '<span class="separator">•</span>' . "\n";
	echo '<a href="' . $_SERVER['SCRIPT_NAME'] . '?day=' . date('j', $timestmpPlusOneDay) . '&amp;month=' . date('n', $timestmpPlusOneDay) . '&amp;year=' . date('Y', $timestmpPlusOneDay) . '&amp;min_editcount=' . $min_editcount . '" title="Auswertung des Folgetages (' . date('j', $timestmpPlusOneDay) . '. ' . $months[intval(date('n', $timestmpPlusOneDay))] . ' ' . date('Y', $timestmpPlusOneDay) . ')">Folgetag</a>' . "\n";
}
echo '</form>' . "\n";
echo '</nav>' . "\n";

// in case of valid input, evaluate result
if(false === $invalid_date){
	$db = new Database($config['replica_dewiki_web_host'], $config['replica_dewiki_dbname']);
	$tooldb = new Database($config['tooldb_host'], $config['tooldb_dbname']);

	$sql0 = 'SELECT * FROM localuser WHERE timestmp_first>=:start AND timestmp_first<=:end';
	$statement0 = $tooldb->getConnection()->prepare($sql0);
	$statement0->bindParam(':start', $start, PDO::PARAM_INT);
	$statement0->bindParam(':end', $end, PDO::PARAM_INT);

//	$sql1; // defined further down; uses "WHERE ... IN (...)", which is not possible with PDO's prepared statements

	$sql2_actor = 'SELECT actor_id FROM actor WHERE actor_user=:actoruser';
	$statement2_actor = $db->getConnection()->prepare($sql2_actor);
	$statement2_actor->bindParam(':actoruser', $userid, PDO::PARAM_INT);

	$sql2_first = 'SELECT rev_timestamp AS first_edit FROM revision_userindex WHERE rev_actor=:actorid ORDER BY rev_timestamp ASC LIMIT 1'; // https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#Tables_for_revision_or_logging_queries_involving_user_names_and_IDs ; see also #wikimedia-cloud archive of 2019-06-05 evening for the actor table
	$statement2_first = $db->getConnection()->prepare($sql2_first);
	$statement2_first->bindParam(':actorid', $actorid, PDO::PARAM_INT);

	$sql2_last = 'SELECT rev_timestamp AS last_edit FROM revision_userindex WHERE rev_actor=:actorid ORDER BY rev_timestamp DESC LIMIT 1';
	$statement2_last = $db->getConnection()->prepare($sql2_last);
	$statement2_last->bindParam(':actorid', $actorid, PDO::PARAM_INT);

//	$sql3; // defined further down; uses "WHERE ... IN (...)", which is not possible with PDO's prepared statements

	$found_any = false;

	foreach($wikilaeums as $wikilaeum => $commonname){
		$dt_start = new DateTime(sprintf('%d-%02d-%02d %02d:%02d:%02d', $year-$wikilaeum, $month, $day, 0, 0, 0), new DateTimeZone($config['timezone']));
		$dt_end = new DateTime(sprintf('%d-%02d-%02d %02d:%02d:%02d', $year-$wikilaeum, $month, $day, 23, 59, 59), new DateTimeZone($config['timezone']));
		$dt_start->setTimezone(new DateTimeZone('UTC'));
		$dt_end->setTimezone(new DateTimeZone('UTC'));
		$dt_noon = new DateTime(sprintf('%d-%02d-%02d %02d:%02d:%02d', $year-$wikilaeum, $month, $day, 12, 0, 0), new DateTimeZone($config['timezone']));
		if($month === intval($dt_noon->format('m'))){ // important to avoid showing results for March 1 on February 29 (i.e. only on leap day, which does not necessarily exist n years earlier)
			$start = intval($dt_start->format('YmdHis'));
			$end = intval($dt_end->format('YmdHis'));
			try {
				$statement0->execute();
				$result0 = $statement0->fetchAll();

				$userids = array();
				$first = array();
				foreach($result0 as $elem){
					$userids[] = intval($elem['user_id']);
					$first[intval($elem['user_id'])] = $elem['timestmp_first'];
				}

				if(count($userids) > 0){
					$sql1 = 'SELECT user.user_id, user.user_name, user.user_editcount, user.user_registration, GROUP_CONCAT(user_groups.ug_group) AS ug_groups FROM user LEFT JOIN user_groups ON user.user_id=user_groups.ug_user WHERE user.user_id IN (' . implode(',', $userids) . ') AND user.user_editcount>=:mineditcount GROUP BY user.user_id, user.user_name, user.user_editcount, user.user_registration ORDER BY user.user_editcount DESC';
					$statement1 = $db->getConnection()->prepare($sql1);
					$statement1->bindParam(':mineditcount', $min_editcount);
					$statement1->execute();
				}

				if($statement0->rowcount() > 0 && $statement1->rowcount() > 0){
					$result1 = $statement1->fetchAll();
					$found_any = true;

					$sql3 = 'SELECT log_title, COUNT(log_id) AS number_of_blocks FROM logging WHERE log_namespace=2 AND log_title IN (SELECT user_name FROM user WHERE user_id IN (' . implode(',', $userids) . ')) AND log_type="block" AND log_action="block" GROUP BY log_title';
	//				$result3 = $db->getConnection()->query($sql3); // poor performance
	//				$blocks = array();
	//				while($row3 = $result3->fetch()){
	//					$blocks[$row3['log_title']] = $row3['number_of_blocks'];
	//				}

					echo '<section>' . "\n";
					echo '<h2>Auszeichnungsstufe <span class="level ' . strtolower($commonname) . '">' . $commonname . '</span> (' . $wikilaeum . ' Jahre)</h2>' . "\n";
					echo '<table class="results ' . strtolower($commonname) . '">' . "\n";
					echo '<thead><tr><th>User</th><th>Links</th><th>Benutzergruppen</th><th>Beiträge</th><th>Anmeldung</th><th>Erster Beitrag</th><th colspan="2">Letzter Beitrag</tr></thead>' . "\n";
					echo '<tbody>' . "\n";
					foreach($result1 as $row1){
						$userid = intval($row1['user_id']);

						$statement2_actor->execute();
						$row2_actor = $statement2_actor->fetchAll();
						$actorid = $row2_actor[0]['actor_id'];

						echo '<tr>';
						echo '<td><a href="https://de.wikipedia.org/wiki/User:' . str_replace(' ', '_', $row1['user_name']) . '" title="Benutzerseite von ' . $row1['user_name'] . '">' . $row1['user_name'] . '</a><!-- user id: ' . $row1['user_id'] . '; actor id: ' . $actorid . ' --></td>';
						echo '<td class="tdcenter"><a href="https://de.wikipedia.org/wiki/User_talk:' . str_replace(' ', '_', $row1['user_name']) . '" title="Diskussionsseite von ' . $row1['user_name'] . '">Diskussion</a> • <a href="https://de.wikipedia.org/wiki/Special:Log/' . str_replace(' ', '_', $row1['user_name']) . '" title="Logbuch zu ' . $row1['user_name'] . '">Logbuch</a> • <a href="https://de.wikipedia.org/w/index.php?title=Spezial%3ALogbuch&amp;type=block&amp;page=User%3A' . str_replace(' ', '_', $row1['user_name']) . '" title="Sperrlog von ' . $row1['user_name'] . '">Sperrlog</a> • <a href="https://xtools.wmflabs.org/ec/dewiki/' . str_replace(' ', '_', $row1['user_name']) . '" title="xtools Beitragszähler für ' . $row1['user_name'] . '">xtools</a> • <a href="https://xtools.wmflabs.org/pages/de.wikipedia.org/' . str_replace(' ', '_', $row1['user_name']) . '" title="Neue Artikel von ' . $row1['user_name'] . '">Artikel</a></td>';
						if($row1['ug_groups'] !== null){
							echo '<td>' . str_replace(',', ', ', $row1['ug_groups']) . '</td>';
						}
						else {
							echo '<td class="na">keine</td>';
						}
						echo '<td class="tdcenter"><a href="https://de.wikipedia.org/wiki/Special:Contributions/' . str_replace(' ', '_', $row1['user_name']) . '" titel="Beiträge von ' . $row1['user_name'] . '">' . $row1['user_editcount'] . '</a></td>';

						if($row1['user_registration'] !== null){
							$reg_timestamp = formatTimestamp($row1['user_registration'], $config['timezone']);
							echo '<td class="tdcenter">' . date('j.', $reg_timestamp) . ' ' . $months[intval(date('n', $reg_timestamp))] . ' ' . date('Y, H:i:s', $reg_timestamp) . '</td>';
						}
						else {
							echo '<td class="tdcenter na">unbekannt</td>';
						}

						$statement2_first->execute();
						$row2_first = $statement2_first->fetchAll();
						$first_timestamp = formatTimestamp($row2_first[0]['first_edit'], $config['timezone']);
						echo '<td class="tdcenter">' . date('j.', $first_timestamp) . ' ' . $months[intval(date('n', $first_timestamp))] . ' ' . date('Y, H:i:s', $first_timestamp) . '</td>';

						$statement2_last->execute();
						$row2_last = $statement2_last->fetchAll();
						$last_timestamp = formatTimestamp($row2_last[0]['last_edit'], $config['timezone']);
						$diff_seconds = time() - $last_timestamp;
						echo '<td class="tdcenter">' . date('j.', $last_timestamp) . ' ' . $months[intval(date('n', $last_timestamp))] . ' ' . date('Y, H:i:s', $last_timestamp) . '</td>';
						echo '<td class="tdcenter">' . printDiffInDays($diff_seconds) . '</td>';
						echo '</tr>' . "\n";
					}
					echo '</tbody>' . "\n";
					echo '</table>' . "\n";
					echo '</section>' . "\n";
				}
			} catch(PDOException $e){
				echo $e->getMessage();
			}
		}
	}

	if($found_any === false){
		echo '<section><p>Keine Auszeichnungskandidaten gefunden.</p></section>' . "\n";
	}

	$statement0 = null;
	$result1 = null;
	$statement2_actor = null;
	$statement2_first = null;
	$statement2_last = null;
	$result3 = null;
	$db = null;
	$tooldb = null;
}

// end of page
echo '<footer>' . "\n";
echo $footer_html . "\n";
echo '</footer>' . "\n";
echo '</body>' . "\n";
echo '</html>';

function formatTimestamp($mwtimestamp, $timezone='Europe/Berlin'){
	$hour = intval(substr($mwtimestamp, 8, 2));
	$minute = intval(substr($mwtimestamp, 10, 2));
	$second = intval(substr($mwtimestamp, 12, 2));
	$year = intval(substr($mwtimestamp, 0, 4));
	$month = intval(substr($mwtimestamp, 4, 2));
	$day = intval(substr($mwtimestamp, 6, 2));

	$date = new DateTime($year . '-' . $month . '-' . $day . ' ' . $hour . ':' . $minute . ':' . $second, new DateTimeZone('UTC'));
	$date->setTimezone(new DateTimeZone($timezone));

	return $date->format('U');
}

function printDiffInDays($seconds){
	$days = bcdiv($seconds, 86400, 0);
	return $days . ' Tag' . ($days !== '1'?'e':'');
}
