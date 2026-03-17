<?php
$log = "";
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($_POST['url'])) {
    $url = escapeshellarg($_POST['url']);
    $output = shell_exec("python downloader.py $url 2>&1");
    $log = "<div class='terminal'><pre>$output</pre></div>";
}
?>
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YTDL FTP</title>
    <style>
        body { font-family: monospace; background: #000; color: #0f0; padding: 20px; }
        .box { border: 1px solid #0f0; padding: 20px; max-width: 500px; margin: auto; }
        input { width: 100%; padding: 10px; background: #111; border: 1px solid #0f0; color: #0f0; margin: 10px 0; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #0f0; color: #000; border: none; cursor: pointer; font-weight: bold; }
        .terminal { margin-top: 20px; font-size: 12px; color: #0f0; border-top: 1px dashed #0f0; }
    </style>
</head>
<body>
    <div class="box">
        <h2>> YTDL TO BYETHOST</h2>
        <form method="post">
            <input type="text" name="url" placeholder="URL do Vídeo" required>
            <button type="submit">BAIXAR E ENVIAR</button>
        </form>
        <?php echo $log; ?>
    </div>
</body>
</html>
