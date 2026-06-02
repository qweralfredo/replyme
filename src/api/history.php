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

$email_id = $_GET['email_id'] ?? null;
if (!$email_id) {
    ResponseFactory::error('email_id is required', 400);
}

try {
    $pdo = Database::getInstance();
    $sql = "SELECT * FROM email_history WHERE email_id = ? ORDER BY created_at ASC";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([$email_id]);
    $items = $stmt->fetchAll();
    
    ResponseFactory::json($items);
} catch (\Exception $e) {
    ResponseFactory::error($e->getMessage(), 500);
}
