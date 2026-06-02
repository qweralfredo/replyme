<?php

class Database {
    private static $instance = null;
    private $pdo;

    private function __construct() {
        // Assume default docker-compose environment variables for now
        $host = getenv('DB_HOST') ?: 'db';
        $port = getenv('DB_PORT') ?: '5432';
        $db   = getenv('DB_NAME') ?: 'replayme_db';
        $user = getenv('DB_USER') ?: 'postgres';
        $pass = getenv('DB_PASS') ?: 'password';

        $dsn = "pgsql:host=$host;port=$port;dbname=$db;";
        try {
            $this->pdo = new PDO($dsn, $user, $pass, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]);
        } catch (\PDOException $e) {
            throw new \Exception($e->getMessage(), (int)$e->getCode());
        }
    }

    public static function getInstance() {
        if (self::$instance == null) {
            self::$instance = new Database();
        }
        return self::$instance->pdo;
    }
}
