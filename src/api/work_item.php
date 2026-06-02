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

try {
    $pdo = Database::getInstance();
    
    // Get current status to log history
    $stmt = $pdo->prepare("SELECT status FROM emails WHERE id = :id");
    $stmt->execute([':id' => $data['id']]);
    $current = $stmt->fetch();
    if (!$current) {
        ResponseFactory::error('Work item not found', 404);
    }
    $old_status = $current['status'];

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

    if (isset($data['status']) && $data['status'] !== $old_status) {
        $hist_sql = "INSERT INTO email_history (email_id, action, from_status, to_status, created_at) VALUES (?, ?, ?, ?, NOW())";
        $hist_stmt = $pdo->prepare($hist_sql);
        $hist_stmt->execute([
            $data['id'],
            "Manual card move",
            $old_status,
            $data['status']
        ]);
    }
    
    ResponseFactory::json($updated);
} catch (\Exception $e) {
    ResponseFactory::error($e->getMessage(), 500);
}
