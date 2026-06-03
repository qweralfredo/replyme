<?php
require_once __DIR__ . '/ResponseFactory.php';
header('Content-Type: application/json');

// Permitir pre-flight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $mcp_id = $input['mcp_id'] ?? null;
    $prompt = $input['prompt'] ?? '';

    if (!$mcp_id || empty($prompt)) {
        ResponseFactory::error("mcp_id and prompt are required", 400);
    }

    // Call Python container logic
    $url = 'http://app:8000/test_mcp';
    $data = json_encode(['mcp_id' => $mcp_id, 'prompt' => $prompt]);

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($data)
    ]);
    
    // Disable timeout basically to allow long LLM running
    curl_setopt($ch, CURLOPT_TIMEOUT, 120);

    $response = curl_exec($ch);
    $httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    
    if (curl_errno($ch)) {
        $error_msg = curl_error($ch);
        curl_close($ch);
        ResponseFactory::error("cURL error: " . $error_msg, 500);
    }
    
    curl_close($ch);

    if ($httpcode !== 200) {
        ResponseFactory::error("Python container returned HTTP " . $httpcode . " : " . $response, 500);
    }

    echo $response;
} else {
    ResponseFactory::error("Method not allowed", 405);
}
