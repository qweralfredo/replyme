<?php

require_once __DIR__ . '/ResponseFactory.php';
require_once __DIR__ . '/Database.php';

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    ResponseFactory::error('Method not allowed', 405);
}

try {
    $pdo = Database::getInstance();
    $sql = "SELECT * FROM emails ORDER BY created_at DESC";
    
    // We could add pagination or filtering here, but for now we return all and group them on frontend or fetch by status.
    $stmt = $pdo->query($sql);
    $items = $stmt->fetchAll();
    
    ResponseFactory::json($items);
} catch (\Exception $e) {
    ResponseFactory::error($e->getMessage(), 500);
}
