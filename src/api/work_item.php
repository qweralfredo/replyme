<?php

require_once __DIR__ . '/ResponseFactory.php';
require_once __DIR__ . '/Database.php';

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: PATCH, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'PATCH') {
    ResponseFactory::error('Method not allowed', 405);
}

$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data || !isset($data['id'])) {
    ResponseFactory::error('ID is required', 400);
}

$valid_statuses = ['inbox', 'processing', 'review', 'done', 'error'];

if (isset($data['status']) && !in_array($data['status'], $valid_statuses)) {
    ResponseFactory::error('Invalid status', 422);
}

try {
    $pdo = Database::getInstance();
    
    // We update status and optionally ai_response if provided
    $updates = [];
    $params = [];
    
    if (isset($data['status'])) {
        $updates[] = "status = :status";
        $params[':status'] = $data['status'];
    }
    
    if (isset($data['ai_response'])) {
        $updates[] = "ai_response = :ai_response";
        $params[':ai_response'] = $data['ai_response'];
    }
    
    if (empty($updates)) {
        ResponseFactory::error('Nothing to update', 400);
    }
    
    $params[':id'] = $data['id'];
    
    $sql = "UPDATE emails SET " . implode(', ', $updates) . " WHERE id = :id RETURNING *";
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    
    $updated = $stmt->fetch();
    
    if (!$updated) {
        ResponseFactory::error('Work item not found', 404);
    }
    
    ResponseFactory::json($updated);
} catch (\Exception $e) {
    ResponseFactory::error($e->getMessage(), 500);
}
