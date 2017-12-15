<?php

class Database {

	private $localdbSqlTables = '../wikilaeum.sql'; // if the local table is missing, set it up from this file
	private $connection;

	function __construct($host, $database){
		try {
			$tooluser = posix_getpwuid(posix_getuid());
			if(false !== ($db_credentials = parse_ini_file($tooluser['dir'] . '/replica.my.cnf', TRUE))){
				$this->connection = new PDO('mysql:host=' . $host . ';dbname=' . $database . ';charset=utf8mb4', $db_credentials['client']['user'], $db_credentials['client']['password']);
				unset($db_credentials, $tooluser);
			}
			else {
				exit('database credentials missing');
			}

			$this->connection->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

			if(substr($host, 0, 5) === 'tools'){
				$result = $this->connection->query('SHOW TABLES')->fetchAll();	// set up tables if not present
				if(in_array('localuser', $result) === false){
					$this->connection->exec(file_get_contents($this->localdbSqlTables));
				}
			}

		} catch(PDOException $e){
			unset($db_credentials, $tooluser);
			die('ERROR: '. $e->getMessage());
		}
	}

	function __destruct(){
		$this->connection = null;
	}

	public function getConnection(){
		return $this->connection;
	}
}
