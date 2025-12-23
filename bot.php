<?php
ob_start();
error_reporting(0);
date_default_timezone_set('Asia/Tashkent');

/*
Ushbu kod @uzanimedia_bot ni asl kodi bo'lib, ushbu kodni @TokhtasinovUz ( Tokhtasinov Saidabror ) tuzib chiqgan.
Mehnatimni qadrlaysz degan umiddaman. Hammaga raxmat !!!
*/

define('API_TOKEN',"7634679212:AAFWbDnbqvLQPF_ayR3E7yAANHrUBuPUL1s");
$obito_us = "8201154770";
$admins = file_get_contents("admin/admins.txt");
$admin = explode("\n",$admins);
$studio_name = file_get_contents("admin/studio_name.txt");
array_push($admin,$obito_us,1476661984);
$user = file_get_contents("admin/user.txt");
$bot = bot('getme',['bot'])->result->username;
$soat = date('H:i');
$sana = date("d.m.Y");

require ("sql.php");

function getAdmin($chat){
$url = "https://api.telegram.org/bot".API_TOKEN."/getChatAdministrators?chat_id=@".$chat;
$result = file_get_contents($url);
$result = json_decode ($result);
return $result->ok;
}

function deleteFolder($path){
if(is_dir($path) === true){
$files = array_diff(scandir($path), array('.', '..'));
foreach ($files as $file)
deleteFolder(realpath($path) . '/' . $file);
return rmdir($path);
}else if (is_file($path) === true)
return unlink($path);
return false;
}

function joinchat($userId, $key = null) {
    static $sent = [];

    global $connect, $bot;

    $statusv = null;
    $res = mysqli_query($connect, "SELECT * FROM `user_id` WHERE `user_id` = '".intval($userId)."' LIMIT 1");
    if ($res && mysqli_num_rows($res) > 0) {
        $a = mysqli_fetch_assoc($res);
        $statusv = $a['status'];
    }

    if ($statusv === "VIP") {
        return true;
    }

    $query = $connect->query("SELECT * FROM `channels`");
    $noSubs = 0;
    $button = [];

    if ($query->num_rows > 0) {
        while ($row = $query->fetch_assoc()) {
            $channelId = $row['channelId'];
            $joined = false;

            if ($row['channelType'] == "request") {
                $checkRequest = $connect->query("SELECT * FROM `joinRequests` WHERE `channelId` = '$channelId' AND `userId` = '$userId'");
                if ($checkRequest && $checkRequest->num_rows > 0) {
                    $joined = true;
                }
            } elseif ($row['channelType'] == "lock") {
                $resStat = bot('getChatMember', [
                    'chat_id' => $channelId,
                    'user_id' => $userId
                ]);

                if (isset($resStat->result->status)) {
                    $stat = $resStat->result->status;
                    if ($stat != "left" && $stat != "kicked") {
                        $joined = true;
                    }
                }
            }

            if (!$joined) {
                $noSubs++;
                $button[] = ['text' => $row['nom'], 'url' => $row['channelLink']];
            }
        }
    }

    $links_file = "admin/links.json";
    if (file_exists($links_file)) {
        $links = json_decode(file_get_contents($links_file), true);
        if (is_array($links) && count($links) > 0) {
            foreach ($links as $link) {
                $button[] = ['text' => $link['name'], 'url' => $link['url']];
            }
        }
    }

    $keyboard = array_chunk($button, 1);
    $keyboard[] = [['text' => "✅ Tekshirish", 'url' => "https://t.me/$bot?start=" . ($key ?? 'null')]];
    $reply_markup = json_encode(['inline_keyboard' => $keyboard]);

    // --- prevent double send in same request ---
    if ($noSubs > 0) {
        if (isset($sent[$userId]) && $sent[$userId] === true) {
            return false;
        }
        sms($userId, "<b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling❗️</b>", $reply_markup);
        $sent[$userId] = true;
        return false;
    } else {
        return true;
    }
}


function accl($d,$s,$j=false){
return bot('answerCallbackQuery',[
'callback_query_id'=>$d,
'text'=>$s,
'show_alert'=>$j
]);
}

function del(){
global $cid,$mid,$cid2,$mid2;
return bot('deleteMessage',[
'chat_id'=>$cid2.$cid,
'message_id'=>$mid2.$mid,
]);
}


function edit($id,$mid,$tx,$m){
return bot('editMessageText',[
'chat_id'=>$id,
'message_id'=>$mid,
'text'=>$tx,
'parse_mode'=>"HTML",
'disable_web_page_preview'=>true,
'reply_markup'=>$m,
]);
}



function sms($id,$tx,$m){
return bot('sendMessage',[
'chat_id'=>$id,
'text'=>$tx,
'parse_mode'=>"HTML",
'disable_web_page_preview'=>true,
'reply_markup'=>$m,
]);
}



function get($h){
return file_get_contents($h);
}

function put($h,$r){
file_put_contents($h,$r);
}

function bot($method,$datas=[]){
	$url = "https://api.telegram.org/bot".API_TOKEN."/".$method;
	$ch = curl_init();
	curl_setopt($ch,CURLOPT_URL,$url);
	curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
	curl_setopt($ch,CURLOPT_POSTFIELDS,$datas);
	$res = curl_exec($ch);
	if(curl_error($ch)){
		var_dump(curl_error($ch));
	}else{
		return json_decode($res);
	}
}

function containsEmoji($string) {
	// Emoji Unicode diapazonlarini belgilash
	$emojiPattern = '/[\x{1F600}-\x{1F64F}]/u'; // Emotikonlar
	$emojiPattern .= '|[\x{1F300}-\x{1F5FF}]'; // Belgilar va piktograflar
	$emojiPattern .= '|[\x{1F680}-\x{1F6FF}]'; // Transport va xaritalar
	$emojiPattern .= '|[\x{1F700}-\x{1F77F}]'; // Alkimyo belgilar
	$emojiPattern .= '|[\x{1F780}-\x{1F7FF}]'; // Har xil belgilar
	$emojiPattern .= '|[\x{1F800}-\x{1F8FF}]'; // Suv belgilari
	$emojiPattern .= '|[\x{1F900}-\x{1F9FF}]'; // Odatdagilar
	$emojiPattern .= '|[\x{1FA00}-\x{1FA6F}]'; // Qisqichbaqasimon belgilar
	$emojiPattern .= '|[\x{2600}-\x{26FF}]';   // Turli xil belgilar va piktograflar
	$emojiPattern .= '|[\x{2700}-\x{27BF}]';   // Dingbatlar
	$emojiPattern .= '/u';
 
	// Regex orqali tekshirish
	return preg_match($emojiPattern, $string) === 1;
}

function removeEmoji($string) {
	// Emoji Unicode diapazonlarini belgilash
	$emojiPattern = '/[\x{1F600}-\x{1F64F}]/u'; // Emotikonlar
	$emojiPattern .= '|[\x{1F300}-\x{1F5FF}]'; // Belgilar va piktograflar
	$emojiPattern .= '|[\x{1F680}-\x{1F6FF}]'; // Transport va xaritalar
	$emojiPattern .= '|[\x{1F700}-\x{1F77F}]'; // Alkimyo belgilar
	$emojiPattern .= '|[\x{1F780}-\x{1F7FF}]'; // Har xil belgilar
	$emojiPattern .= '|[\x{1F800}-\x{1F8FF}]'; // Suv belgilari
	$emojiPattern .= '|[\x{1F900}-\x{1F9FF}]'; // Odatdagilar
	$emojiPattern .= '|[\x{1FA00}-\x{1FA6F}]'; // Qisqichbaqasimon belgilar
	$emojiPattern .= '|[\x{2600}-\x{26FF}]';   // Turli xil belgilar va piktograflar
	$emojiPattern .= '|[\x{2700}-\x{27BF}]';   // Dingbatlar
	$emojiPattern .= '/u';
 
	// Regex orqali tekshirish
	return preg_replace($emojiPattern, '', $string);
}

function adminsAlert($message){
global $admin;
foreach($admin as $adm){
sms($adm,$message,null);
}
}

$alijonov = json_decode(file_get_contents('php://input'));
$message = $alijonov->message;
$cid = $message->chat->id;
$name = $message->chat->first_name;
$tx = $message->text;
$step = file_get_contents("step/$cid.step");
$mid = $message->message_id;
$type = $message->chat->type;
$text = $message->text;
$uid= $message->from->id;
$name = $message->from->first_name;
$familya = $message->from->last_name;
$bio = $message->from->about;
$username = $message->from->username;
$chat_id = $message->chat->id;
$message_id = $message->message_id;
$reply = $message->reply_to_message->text;
$nameru = "<a href='tg://user?id=$uid'>$name $familya</a>";

$botdel = $alijonov->my_chat_member->new_chat_member; 
$botdelid = $alijonov->my_chat_member->from->id; 
$userstatus= $botdel->status; 

$update = json_decode(file_get_contents('php://input'));

if (isset($update->chat_join_request)) {
    $chatId = $update->chat_join_request->chat->id;
    $userId = $update->chat_join_request->from->id;

    $check = $connect->query("SELECT * FROM joinRequests WHERE channelId = '$chatId' AND userId = '$userId'");
    if ($check->num_rows === 0) {
        $connect->query("INSERT INTO joinRequests (channelId, userId) VALUES ('$chatId', '$userId')");
    }

} elseif (isset($update->message)) {
    $userId = $update->message->from->id;

    $channels = $connect->query("SELECT channelId FROM channels WHERE channelType = 'request'");
    if ($channels->num_rows > 0) {
        while ($row = $channels->fetch_assoc()) {
            $chatId = $row['channelId'];

            $check = $connect->query("SELECT * FROM joinRequests WHERE channelId = '$chatId' AND userId = '$userId'");
            if ($check->num_rows === 0) {
                $chatMember = bot('getChatMember', [
                    'chat_id' => $chatId,
                    'user_id' => $userId
                ]);

                $status = $chatMember->result->status ?? null;

                if (in_array($status, ['administrator', 'creator'])) {
                    $connect->query("INSERT INTO joinRequests (channelId, userId) VALUES ('$chatId', '$userId')");
                }
            }
        }
    }
}

//inline uchun metodlar
$data = $alijonov->callback_query->data;
$qid = $alijonov->callback_query->id;
$id = $alijonov->inline_query->id;
$query = $alijonov->inline_query->query;
$query_id = $alijonov->inline_query->from->id;
$cid2 = $alijonov->callback_query->message->chat->id;
$mid2 = $alijonov->callback_query->message->message_id;
$callfrid = $alijonov->callback_query->from->id;
$callname = $alijonov->callback_query->from->first_name;
$calluser = $alijonov->callback_query->from->username;
$surname = $alijonov->callback_query->from->last_name;
$about = $alijonov->callback_query->from->about;
$nameuz = "<a href='tg://user?id=$callfrid'>$callname $surname</a>";

if(isset($data)){
$chat_id=$cid2;
$message_id=$mid2;
}

$photo = $message->photo;
$file = $photo[count($photo)-1]->file_id;

//tugmalar
if(file_get_contents("tugma/key1.txt")){
	}else{
		if(file_put_contents("tugma/key1.txt","🔎 Anime izlash"));
	}
if(file_get_contents("tugma/key2.txt")){
	}else{
		if(file_put_contents("tugma/key2.txt","💎 VIP"));
	}
if(file_get_contents("tugma/key3.txt")){
	}else{
		if(file_put_contents("tugma/key3.txt","💰 Hisobim"));
	}
if(file_get_contents("tugma/key4.txt")){
	}else{
		if(file_put_contents("tugma/key4.txt","➕ Pul kiritish"));
	}
if(file_get_contents("tugma/key5.txt")){
	}else{
		if(file_put_contents("tugma/key5.txt","📚 Qo'llanma"));
	}
if(file_get_contents("tugma/key6.txt")){
	}else{
		if(file_put_contents("tugma/key6.txt","💵 Reklama va Homiylik"));
	}
	
//pul va referal sozlamalar

if(file_get_contents("admin/valyuta.txt")){
	}else{
		if(file_put_contents("admin/valyuta.txt","so'm"));
}

if(file_get_contents("admin/vip.txt")){
	}else{
		if(file_put_contents("admin/vip.txt","25000"));
}

if(file_get_contents("admin/holat.txt")){
	}else{
		if(file_put_contents("admin/holat.txt","Yoqilgan"));
}

if(file_exists("admin/anime_kanal.txt")==false){
file_put_contents("admin/anime_kanal.txt","@username");
}

//matnlar
if(file_get_contents("matn/start.txt")){
}else{
if(file_put_contents("matn/start.txt","✨"));
}

$res = mysqli_query($connect,"SELECT*FROM user_id WHERE user_id=$chat_id");
while($a = mysqli_fetch_assoc($res)){
$user_id = $a['user_id'];
$status = $a['status'];
$taklid_id = $a['refid'];
$from_id = $a['id'];
$usana = $a['sana'];
}

$res = mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id=$chat_id");
while($a = mysqli_fetch_assoc($res)){
$k_id = $a['user_id'];
$pul = $a['pul'];
$pul2 = $a['pul2'];
$odam = $a['odam'];
$ban = $a['ban'];
}

$key1 = file_get_contents("tugma/key1.txt");
$key2 = file_get_contents("tugma/key2.txt");
$key3 = file_get_contents("tugma/key3.txt");
$key4 = file_get_contents("tugma/key4.txt");
$key5 = file_get_contents("tugma/key5.txt");
$key6 = file_get_contents("tugma/key6.txt");

$test = file_get_contents("step/test.txt");
$test1 = file_get_contents("step/test1.txt");
$test2 = file_get_contents("step/test2.txt");
$turi = file_get_contents("tizim/turi.txt");
$anime_kanal = file_get_contents("admin/anime_kanal.txt");

$narx = file_get_contents("admin/vip.txt");
$kanal = file_get_contents("admin/kanal.txt");
$valyuta = file_get_contents("admin/valyuta.txt");
$start = str_replace(["%first%","%id%","%botname%","%hour%","%date%"], [$name,$cid,$bot,$soat,$sana],file_get_contents("matn/start.txt"));
$qollanma = str_replace(["%first%","%id%","%hour%","%date%","%user%","%botname%",], [$name,$cid,$soat,$sana,$user,$bot],file_get_contents("matn/qollanma.txt"));
$from_id = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM user_id WHERE user_id = $cid2"))['id'];
$pul3 = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $cid2"))['pul'];
$odam2 = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $cid2"))['odam'];
$photo = file_get_contents("matn/photo.txt");
$homiy = file_get_contents("matn/homiy.txt");
$holat = file_get_contents("admin/holat.txt");

mkdir("tizim");
mkdir("step");
mkdir("admin");
mkdir("tugma");
mkdir("matn");

$panel = json_encode([
'resize_keyboard'=>true,
'keyboard'=>[
[['text'=>"*️⃣ Birlamchi sozlamalar"]],
[['text'=>"📊 Statistika"],['text'=>"✉ Xabar Yuborish"]],
[['text'=>"📬 Post tayyorlash"]],
[['text'=>"🎥 Animelar sozlash"],['text'=>"💳 Hamyonlar"]],
[['text'=>"🔎 Foydalanuvchini boshqarish"]],
[['text'=>"📢 Kanallar"],['text'=>"🎛 Tugmalar"],['text'=>"📃 Matnlar"]],
[['text'=>"📋 Adminlar"],['text'=>"🤖 Bot holati"]],
[['text'=>"◀️ Orqaga"]]
]
]);

$asosiy = $panel;

$menu = json_encode([
'resize_keyboard'=>true,
'keyboard'=>[
[['text'=>"$key1"]],
[['text'=>"$key2"],['text'=>"$key3"]],
[['text'=>"$key4"],['text'=>"$key5"]],
[['text'=>"$key6"]],
]
]);

$menus = json_encode([
'resize_keyboard'=>true,
'keyboard'=>[
[['text'=>"$key1"]],
[['text'=>"$key2"],['text'=>"$key3"]],
[['text'=>"$key4"],['text'=>"$key5"]],
[['text'=>"$key6"]],
[['text'=>"🗄 Boshqarish"]],
]
]);

$back = json_encode([
'resize_keyboard'=>true,
'keyboard'=>[
[['text'=>"◀️ Orqaga"]],
]
]);

$boshqarish = json_encode([
'resize_keyboard'=>true,
'keyboard'=>[
[['text'=>"🗄 Boshqarish"]],
]
]);

if(in_array($cid,$admin)){
$menyu = $menus;
}else{
$menyu = $menu;
}

if(in_array($cid2,$admin)){
$menyus = $menus;
}else{
$menyus = $menu;
}

//<---- @AlijonovUz ---->//
if($text){
if($ban == "ban"){
exit();
}
}

if($data){
$ban = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $cid2"))['ban'];
	if($ban == "ban"){
	exit();
}
}

if(isset($message)){
if(!$connect){
bot('sendMessage',[
'chat_id' =>$cid,
'text'=>"⚠️ <b>Xatolik!</b>

<i>Botdan ro'yxatdan o'tish uchun, /start buyrug'ini yuboring!</i>",
'parse_mode' =>'html',
]);
exit();
}
}

if($text){
 if($holat == "O'chirilgan"){
	if(in_array($cid,$admin)){
}else{
	bot('sendMessage',[
	'chat_id'=>$cid,
	'text'=>"⛔️ <b>Bot vaqtinchalik o'chirilgan!</b>

<i>Botda ta'mirlash ishlari olib borilayotgan bo'lishi mumkin!</i>",
'parse_mode'=>'html',
]);
exit();
}
}
}

if($data){
 if($holat == "O'chirilgan"){
	if(in_array($cid2,$admin)){
}else{
	bot('answerCallbackQuery',[
		'callback_query_id'=>$qid,
		'text'=>"⛔️ Bot vaqtinchalik o'chirilgan!

Botda ta'mirlash ishlari olib borilayotgan bo'lishi mumkin!",
		'show_alert'=>true,
		]);
exit();
}
}
}

if(isset($message)){
$result = mysqli_query($connect,"SELECT * FROM user_id WHERE user_id = $cid");
$row = mysqli_fetch_assoc($result);
if(!$row){
mysqli_query($connect,"INSERT INTO user_id(`user_id`,`status`,`sana`) VALUES ('$cid','Oddiy','$sana')");
}
}

if(isset($message)){
$result = mysqli_query($connect,"SELECT * FROM kabinet WHERE user_id = $cid");
$row = mysqli_fetch_assoc($result);
if(!$row){
mysqli_query($connect,"INSERT INTO kabinet(`user_id`,`pul`,`pul2`,`odam`,`ban`) VALUES ('$cid','0','0','0','unban')");
}
}

if($text == "/start" or $text=="◀️ Orqaga"){	
sms($cid,$start,$menyu);
unlink("step/$cid.step");
exit();
}

if($data == "result"){
del();
if(joinchat($cid2)==true){
sms($cid2,$start,$menyu);
exit();
}
}

//<---- @AlijonovUz ---->//

if(mb_stripos($text,"/start ")!==false and $text != "/start anipass"){
$id = str_replace('/start ','',$text);
if(joinchat($cid,$id)==1){
$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM animelar WHERE id = $id"));
if($rew){
$cs = $rew['qidiruv'] + 1;
mysqli_query($connect,"UPDATE animelar SET qidiruv = $cs WHERE id = $id");
bot('sendPhoto',[
'chat_id'=>$cid,
'photo'=>$rew['rams'],
'caption'=>"<b>🎬 Nomi: $rew[nom]</b>

🎥 Qismi: $rew[qismi]
🌍 Davlati: $rew[davlat]
🇺🇿 Tili: $rew[tili]
📆 Yili: $rew[yili]
🎞 Janri: $rew[janri]

🔍Qidirishlar soni: $cs

🍿 $anime_kanal",
'parse_mode'=>"html",
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"YUKLAB OLISH 📥",'callback_data'=>"yuklanolish=$id=1"]]
]
])
]);
exit();
}else{
sms($cid,$start,$menyu);
exit();
}
}
}



if($data=="close")del();

if($text == $key1 and joinchat($cid)==1){
sms($cid,"<b>🔍Qidiruv tipini tanlang :</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"🏷Anime nomi orqali",'callback_data'=>"searchByName"],['text'=>"⏱ So'ngi yuklanganlar",'callback_data'=>"lastUploads"]],
[['text'=>"💬Janr orqali qidirish",'callback_data'=>"searchByGenre"]],
[['text'=>"📌Kod orqali",'callback_data'=>"searchByCode"],['text'=>"👁️ Eng ko'p ko'rilgan",'callback_data'=>"topViewers"]],
[['text'=>"📚Barcha animelar",'callback_data'=>"allAnimes"]]
]]));
exit();
}

if($data=="searchByName"){
sms($cid2,"<b>Anime nomini yuboring:</b>",$back);
exit();
}

if($data=="lastUploads"){
if($status=="VIP"){
$a =$connect->query("SELECT * FROM `animelar` ORDER BY `sana` DESC LIMIT 0,10");
$i=1;
while($s = mysqli_fetch_assoc($a)){
$uz[] = ['text'=>"$i - $s[nom]",'callback_data'=>"loadAnime=$s[id]"];
}
$keyboard2=array_chunk($uz,1);
$kb=json_encode([
'inline_keyboard'=>$keyboard2,
]);
edit($cid2,$mid2,"<b>⬇️ Qidiruv natijalari:</b>",$kb);
exit();
}else{
bot('answerCallbackQuery',[
'callback_query_id'=>$qid,
'text'=>"Ushbu funksiyadan foydalanish uchun $key2 sotib olishingiz zarur!",
'show_alert'=>true,
]);
}
}

if($data=="topViewers"){
if($status=="VIP"){
$a =$connect->query("SELECT * FROM `animelar` ORDER BY `qidiruv` ASC LIMIT 0,10");
$i=1;
while($s = mysqli_fetch_assoc($a)){
$uz[] = ['text'=>"$i - $s[nom]",'callback_data'=>"loadAnime=$s[id]"];
$i++;
}
$keyboard2=array_chunk($uz,1);
$kb=json_encode([
'inline_keyboard'=>$keyboard2,
]);
edit($cid2,$mid2,"<b>⬇️ Qidiruv natijalari:</b>",$kb);
exit();
}else{
bot('answerCallbackQuery',[
'callback_query_id'=>$qid,
'text'=>"Ushbu funksiyadan foydalanish uchun $key2 sotib olishingiz zarur!",
'show_alert'=>true,
]);
}
}

if(mb_stripos($data,"loadAnime=")!==false){
$n=explode("=",$data)[1];
del();
$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM animelar WHERE id = $n"));
$a = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM `anime_datas` WHERE `id` = $n ORDER BY `qism` ASC LIMIT 1"));
if(in_array($cid2,$admin)) $delKey="🗑️ O‘chirish";
bot('sendPhoto',[
'chat_id'=>$cid2,
'photo'=>$rew['rams'],
'caption'=>"<b>🎬 Nomi: $rew[nom]</b>

🎥 Qismi: $rew[qismi]
🌍 Davlati: $rew[davlat]
🇺🇿 Tili: $rew[tili]
📆 Yili: $rew[yili]
🎞 Janri: $rew[janri]

🔍Qidirishlar soni: $rew[qidiruv]

🍿 $anime_kanal",
'parse_mode'=>"html",
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"YUKLAB OLISH 📥",'callback_data'=>"yuklanolish=$n=$a[qism]"]],
[['text'=>"$delKey",'callback_data'=>"deleteAnime=$n=1"]],
]
])
]);
}

if(mb_stripos($data,"deleteAnime=")!==false){
$n=explode("=",$data)[1];
$res=explode("=",$data)[2];
if($res=="1"){
del();
sms($cid2,"<b>❗O‘chirishga ishonchingiz komilmi?</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"✅ Tasdiqlash",'callback_data'=>"deleteEpisode=$n=$nid=2"]],
[['text'=>"🔙 Orqaga",'callback_data'=>"yuklanolish=$n=$nid"]]
]]));
}elseif($res=="2"){
mysqli_query($connect,"DELETE FROM animelar WHERE id = $n");
mysqli_query($connect,"DELETE FROM anime_datas WHERE id = $n");
del();
sms($cid2,"<b>Bosh menyuga qaytdingiz,</b> anime o‘chirildi!",null);
}
}

if(mb_stripos($data,"yuklanolish=")!==false){
$n=explode("=",$data)[1];
$nid=explode("=",$data)[2];
$last=explode("=",$data)[3];
$curr=ceil($nid/25)*25;
$nn=$curr-25;
del();
if(isset($last)){
$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM anime_datas WHERE id = $n AND qism = $last"));
bot('sendVideo',[
'chat_id'=>$cid2,
'video'=>$rew['file_id'],
'caption'=>"<b>$cnom</b>

$last-qism",
'parse_mode'=>"html"
]);
}else{
$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM animelar WHERE id = $n"));
bot('sendPhoto',[
'chat_id'=>$cid2,
'photo'=>$rew['rams'],
'caption'=>"<b>🎬 Nomi: $rew[nom]</b>

🎥 Qismi: $rew[qismi]
🌍 Davlati: $rew[davlat]
🇺🇿 Tili: $rew[tili]
📆 Yili: $rew[yili]
🎞 Janri: $rew[janri]

🔍Qidirishlar soni: $rew[qidiruv]

🍿 $anime_kanal",
'parse_mode'=>"html"
]);
}

$cc = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM animelar WHERE id = $n"));
$cnom = $cc['nom'];

$rew = mysqli_query($connect,"SELECT * FROM anime_datas WHERE id = $n LIMIT $nn,25");
while($a = mysqli_fetch_assoc($rew)){
if($a['qism']==$nid){
$k[]=['text'=>"[💽] - $a[qism]",'callback_data'=>"null"];
}else{
$k[]=['text'=>"$a[qism]",'callback_data'=>"yuklanolish=$n=$a[qism]=$nid"];
}
}

$keyboard2=array_chunk($k,3);
if(in_array($cid2,$admin)) $keyboard2[]=[['text'=>"🗑️ $nid-qismni o'chrish",'callback_data'=>"deleteEpisode=$n=$nid=1"]];
$keyboard2[]=[['text'=>"⬅️",'callback_data'=>"pagenation=$n=$nid=back"],['text'=>"❌",'callback_data'=>"close"],['text'=>"➡️",'callback_data'=>"pagenation=$n=$nid=next"]];
$kb=json_encode([
'inline_keyboard'=>$keyboard2,
]);

$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM anime_datas WHERE id = $n AND qism = $nid"));
$res = bot('sendVideo',[
'chat_id'=>$cid2,
'video'=>$rew['file_id'],
'caption'=>"<b>$cnom</b>

$nid-qism",
'parse_mode'=>"html",
'reply_markup'=>$kb
]);
}

if(mb_stripos($data,"deleteEpisode=")!==false){
$n=explode("=",$data)[1];
$nid=explode("=",$data)[2];
$res=explode("=",$data)[3];
if($res=="1"){
del();
sms($cid2,"<b>❗O‘chirishga ishonchingiz komilmi?</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"✅ Tasdiqlash",'callback_data'=>"deleteEpisode=$n=$nid=2"]],
[['text'=>"🔙 Orqaga",'callback_data'=>"yuklanolish=$n=$nid"]]
]]));
}elseif($res=="2"){
mysqli_query($connect,"DELETE FROM anime_datas WHERE id = $n AND qism = $nid");
del();
sms($cid2,"<b>Bosh menyuga qaytdingiz,</b> animening $nid-qismi o‘chirildi!",null);
}
}

if(mb_stripos($data,"pagenation=")!==false){
$n=explode("=",$data)[1];
$nid=explode("=",$data)[2];
$tip=explode("=",$data)[3];
$curr=ceil($nid/25)*25;
if($tip=="back")$nn=$curr-25;
if($tip=="next")$nn=$curr+25;

$cc = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM animelar WHERE id = $n"));
$cnom = $cc['nom'];

$rew = mysqli_query($connect,"SELECT * FROM anime_datas WHERE id = $n ASC LIMIT $nn,25");
$c = mysqli_num_rows($rew);
while($a = mysqli_fetch_assoc($rew)){
if($a['qism']==$nid){
$k[]=['text'=>"[$a[qism]] - 💽",'callback_data'=>"null"];
}else{
$k[]=['text'=>"$a[qism]",'callback_data'=>"yuklanolish=$n=$a[qism]"];
}
}

$keyboard2=array_chunk($k,3);
$keyboard2[]=[['text'=>"⬅️",'callback_data'=>"pagenation=$n=$nid=back"],['text'=>"❌",'callback_data'=>"close"],['text'=>"➡️",'callback_data'=>"pagenation=$n=$nid=next"]];
$kb=json_encode([
'inline_keyboard'=>$keyboard2,
]);

if(!$c){
accl($qid,"💔 Topilmadi",1);
}else{
$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM anime_datas WHERE id = $n AND qism = $nn"));
$res = bot('sendVideo',[
'chat_id'=>$cid2,
'video'=>$rew['file_id'],
'caption'=>"<b>$cnom</b>

$nid-qism",
'parse_mode'=>"html",
'reply_markup'=>$kb
]);
}
}

if($data=="allAnimes"){
$result = mysqli_query($connect,"SELECT * FROM animelar");
$count = mysqli_num_rows($result);
$text = "$bot anime botida mavjud bo'lgan barcha animelar ro'yxati 
Barcha animelar soni : $count ta\n\n";
$counter = 1;
while($row = mysqli_fetch_assoc($result)){
$text .= "---- | $counter | ----
Anime kodi : $row[id]
Nomi : $row[nom]
Janri : $row[janri]\n\n";
$counter++;
}
put("step/animes_list_$cid2.txt",$text);
del();
bot('sendDocument',[
'chat_id'=>$cid2,
'document'=>new CURLFile("step/animes_list_$cid2.txt"),
'caption'=>"<b>📝{$bot} Anime botida mavjud bo'lgan $count ta animening ro'yxati</b>",
'parse_mode'=>"html"
]);
unlink("step/animes_list_$cid2.txt");
}

if($data=="searchByCode"){
del();
sms($cid2,"<b>📌 Anime kodini kiriting:</b>",$back);
put("step/$cid2.step",$data);
}


if($step=="searchByCode"){
$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM animelar WHERE id = $text"));
if($rew){
$cs = $rew['qidiruv'] + 1;
mysqli_query($connect,"UPDATE animelar SET qidiruv = $cs WHERE id = $text");
bot('sendPhoto',[
'chat_id'=>$cid,
'photo'=>$rew['rams'],
'caption'=>"<b>🎬 Nomi: $rew[nom]</b>

🎥 Qismi: $rew[qismi]
🌍 Davlati: $rew[davlat]
🇺🇿 Tili: $rew[tili]
📆 Yili: $rew[yili]
🎞 Janri: $rew[janri]

🔍Qidirishlar soni: $cs

🍿 $anime_kanal",
'parse_mode'=>"html",
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"YUKLAB OLISH 📥",'callback_data'=>"yuklanolish=$text=1"]]
]
])
]);
exit();
}else{
sms($cid,"<b>[ $text ] kodiga tegishli anime topilmadi😔</b>

• Boshqa Kod yuboring",null);
exit();
}
}

if($data=="searchByGenre"){
if($status=="VIP"){
del();
sms($cid2,"<b>🔍 Qidirish uchun anime janrini yuboring.</b>
📌Namuna: Syonen",$back);
put("step/$cid2.step",$data);
}else{
bot('answerCallbackQuery',[
'callback_query_id'=>$qid,
'text'=>"Ushbu funksiyadan foydalanish uchun $key2 sotib olishingiz zarur!",
'show_alert'=>true,
]);
}
}

if($step=="searchByGenre"){
if(isset($text)){
$text = mysqli_real_escape_string($connect,$text);
$rew = mysqli_query($connect,"SELECT * FROM animelar WHERE janri LIKE '%$text%' LIMIT 0,10");
$c = mysqli_num_rows($rew);
$i = 1;
while($a = mysqli_fetch_assoc($rew)){
$k[]=['text'=>"$i. $a[nom]",'callback_data'=>"loadAnime=".$a['id']];
$i++;
}
$keyboard2=array_chunk($k,1);
$kb=json_encode([
'inline_keyboard'=>$keyboard2,
]);
if(!$c){
sms($cid,"<b>[ $text ] jariga tegishli anime topilmadi😔</b>

• Boshqa janrni alohida yuboring",null);
exit();
}else{
bot('sendMessage',[
'chat_id'=>$cid,
'reply_to_message_id'=>$mid,
'text'=>"<b>⬇️ Qidiruv natijalari:</b>",
'parse_mode'=>"html",
'reply_markup'=>$kb
]);
exit();
}
}
}

// <---- @obito_us ---->

if(($text == $key2 or $text == "/start anipass") and joinchat($cid)==1){
if($status == "Oddiy"){
sms($cid,"<b>$key2'ga ulanish

{$key2}da qanday imkoniyatlar bor?
• VIP kanal uchun 1martalik havola beriladi
• Hech qanday reklamalarsiz botdan foydalanasiz
• Majburiy obunalik soʻralmaydi</b>

$key2 haqida batafsil Qo'llanma boʻlimidan olishiz mumkin!",json_encode([
'inline_keyboard'=>[
[['text'=>"30 kun - $narx $valyuta",'callback_data'=>"shop=30"]],
[['text'=>"60 kun - ".($narx*2)." $valyuta",'callback_data'=>"shop=60"]],
[['text'=>"90 kun - ".($narx*3)." $valyuta",'callback_data'=>"shop=90"]],
]]));
exit();
}else{
$aktiv_kun = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM `status` WHERE user_id = $cid"))['kun'];
$expire=date('d.m.Y',strtotime("+$aktiv_kun days"));
sms($cid,"<b>Siz $key2 sotib olgansiz!</b>

⏳ Amal qilish muddati $expire gacha",json_encode([
'inline_keyboard'=>[
[['text'=>"🗓️ Uzaytirish",'callback_data'=>"uzaytirish"]],
]]));
exit();
}
}

if($data=="uzaytirish"){
edit($cid2,$mid2,"<b>❗ Obunani necha kunga uzaytirmoqchisiz?</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"30 kun - $narx $valyuta",'callback_data'=>"shop=30"]],
[['text'=>"60 kun - ".($narx*2)." $valyuta",'callback_data'=>"shop=60"]],
[['text'=>"90 kun - ".($narx*3)." $valyuta",'callback_data'=>"shop=90"]],
]]));
exit();
}

if(mb_stripos($data,"shop=")!==false){
$kun = explode("=",$data)[1];
$narx /= 30;
$narx *= $kun;
$pul = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $cid2"))['pul'];
if($pul >= $narx){	
if($status == "Oddiy"){
$date = date('d');
mysqli_query($connect,"INSERT INTO `status` (`user_id`,`kun`,`date`) VALUES ('$cid2', '$kun', '$date')");
mysqli_query($connect,"UPDATE `user_id` SET `status` = 'VIP' WHERE user_id = $cid2");
$a = $pul - $narx;
mysqli_query($connect,"UPDATE kabinet SET pul = $a WHERE user_id = $cid2");
edit($cid2,$mid2,"<b>💎 VIP - statusga muvaffaqiyatli o'tdingiz.</b>",null);
adminsAlert("<a href='tg://user?id=$cid2'>Foydalanuvchi</a> $kun kunlik obuna sotib oldi!");
}else{
$aktiv_kun = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM `status` WHERE user_id = $cid2"))['kun'];
$kun = $aktiv_kun + $kun;
mysqli_query($connect,"UPDATE `status` SET kun = '$kun' WHERE user_id = $cid2");
$a = $pul - $narx;
mysqli_query($connect,"UPDATE kabinet SET pul = $a WHERE user_id = $cid2");
edit($cid2,$mid2,"<b>💎 VIP - statusni muvaffaqiyatli uzaytirdingiz.</b>",null);
}	
}else{
bot('answerCallbackQuery',[
'callback_query_id'=>$qid,
'text'=>"Hisobingizda yetarli mablag' mavjud emas!",
'show_alert'=>true,
]);
}
}

if($text == $key3 and joinchat($cid)==true){
sms($cid,"#ID: <code>$cid</code>
Balans: $pul $valyuta",null);
exit();
}



if($_GET['update']=="vip"){
$res = mysqli_query($connect, "SELECT * FROM `status`");
while($a = mysqli_fetch_assoc($res)){
$id = $a['user_id'];
$kun = $a['kun'];
$date = $a['date'];
if($date != date('d')){
$day = $kun - 1;
$bugun = date('d');
if($day == "0"){
mysqli_query($connect, "DELETE `status` WHERE user_id = $id");
mysqli_query($connect,"UPDATE `user_id` SET `status` = 'Oddiy' WHERE user_id = $id");
}else{
mysqli_query($connect, "UPDATE `status` SET kun='$day',`date`='$bugun' WHERE user_id = $id");
}
}
}
echo json_encode(['status'=>true,'cron'=>"VIP users"]);
}

//<---- @AlijonovUz ---->//

if($text == "➕ Pul kiritish" and joinchat($cid)==1){
if($turi == null){
sms($cid,"😔 To'lov tizimlari topilmadi!",null);
exit();
}else{
$turi = file_get_contents("tizim/turi.txt");
$more = explode("\n",$turi);
$soni = substr_count($turi,"\n");
$keys=[];
for ($for = 1; $for <= $soni; $for++) {
$title=str_replace("\n","",$more[$for]);
$keys[]=["text"=>"$title","callback_data"=>"pay-$title"];
}
$keysboard2 = array_chunk($keys,2);
$payment = json_encode([
'inline_keyboard'=>$keysboard2,
]);
sms($cid,"<b>💳 To'lov tizimlarni birini tanlang:</b>",$payment);
exit();
}
}

if($data == "orqa"){
$turi = file_get_contents("tizim/turi.txt");
$more = explode("\n",$turi);
$soni = substr_count($turi,"\n");
$keys=[];
for ($for = 1; $for <= $soni; $for++) {
$title=str_replace("\n","",$more[$for]);
$keys[]=["text"=>"$title","callback_data"=>"pay-$title"];
$keysboard2 = array_chunk($keys,2);
$payment = json_encode([
'inline_keyboard'=>$keysboard2,
]);
}
edit($cid2,$mid2,"Quidagilardan birini tanlang:",$payment);
}

if(mb_stripos($data, "pay-")!==false){
$ex = explode("-",$data);
$turi = $ex[1];
$addition = file_get_contents("tizim/$turi/addition.txt");
$wallet = file_get_contents("tizim/$turi/wallet.txt");
edit($cid2,$mid2,"<b>💳 To'lov tizimi:</b> $turi

	<b>Hamyon:</b> <code>$wallet</code>
	<b>Izoh:</b> <code>$cid2</code>

$addition",json_encode([
'inline_keyboard'=>[
[['text'=>"☎️ Administator",'url'=>"tg://user?id=$obito_us"]],
[['text'=>"◀️ Orqaga",'callback_data'=>"orqa"]],
]]));
}

if($text == $key5 and joinchat($cid)==1){
if($qollanma == null){
sms($cid,"<b>🙁 Qo'llanma qo'shilmagan!</b>",null);
exit();
}else{
sms($cid,$qollanma,null);
exit();
}
}

if($text == $key6 and joinchat($cid)==1){
if($homiy == null){
sms($cid,"<b>🙁 Homiylik qo'shilmagan!</b>",null);
exit();
}else{
sms($cid,$homiy,json_encode([
'inline_keyboard'=>[
[['text'=>"☎️ Administrator",'url'=>"tg://user?id=$obito_us"]]
]]));
exit();
}
}

//<----- Admin Panel ------>

if($text == "🗄 Boshqarish"){
if(in_array($cid,$admin)){
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Admin paneliga xush kelibsiz!</b>",
'parse_mode'=>'html',
'reply_markup'=>$panel,
]);
unlink("step/$cid.step");
unlink("step/test.txt");
unlink("step/$cid.txt");
exit();
}
}

if($data == "boshqarish"){
	bot('deleteMessage',[
	'chat_id'=>$cid2,
	'message_id'=>$mid2,
	]);
	bot('SendMessage',[
	'chat_id'=>$cid2,
	'text'=>"<b>Admin paneliga xush kelibsiz!</b>",
	'parse_mode'=>'html',
	'reply_markup'=>$panel,
	]);
	exit();
}

if($text == "📬 Post tayyorlash" and in_array($cid,$admin)){
sms($cid,"<b>🆔 Anime kodini kiriting:</b>",$boshqarish);
put("step/$cid.step",'createPost');
exit();
}

if($step == "createPost" and in_array($cid,$admin)){
$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM animelar WHERE id = $text"));
if($rew){
bot('sendPhoto',[
'chat_id'=>$cid,
'photo'=>$rew['rams'],
'caption'=>"<b>✽ ──...──:•°⛩°•:──...──╮
🏷Anime nomi : $rew[nom]
. . . . . . . . . . . . . . . . . . . . . . . ──
🖋Janri :</b>  $rew[janri]
<b>. . . ── . . . . . . . . . . . . . . . . . . . .
🎞Qismlar soni :</b> $rew[qismi]
<b>. . . . . . . . . . . . . . . . . . . . . . . ──
🎙Ovoz berdi : </b>$studio_name
<b>. . . ── . . . . . . . . . . . . . . . . . . . .
💭Tili :</b>  $rew[tili]",
'parse_mode'=>"html",
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"🔹 Tomosha qilish 🔹",'url'=>"https://t.me/$bot?start=$text"]],
[['text'=>"$anime_kanal'ga yuborish",'callback_data'=>"smstoanime_kanal=$text"]]
]
])
]);
sms($cid,"<b>Postingiz tayyorlandi!</b>",$panel);
unlink("step/$cid.step");
exit();
}else{
sms($cid,"<b>[ $text ] kodiga tegishli anime topilmadi😔</b>

• Boshqa Kod yuboring",null);
exit();
}
}

if(mb_stripos($data,"smstoanime_kanal=")!==false){
$text = explode("=",$data)[1];
$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM animelar WHERE id = $text"));
bot('sendPhoto',[
'chat_id'=>$anime_kanal,
'photo'=>$rew['rams'],
'caption'=>"<b>✽ ──...──:•°⛩°•:──...──╮
🏷Anime nomi : $rew[nom]
. . . . . . . . . . . . . . . . . . . . . . . ──
🖋Janri :</b>  $rew[janri]
<b>. . . ── . . . . . . . . . . . . . . . . . . . .
🎞Qismlar soni :</b> $rew[qismi]
<b>. . . . . . . . . . . . . . . . . . . . . . . ──
🎙Ovoz berdi : </b>$studio_name
<b>. . . ── . . . . . . . . . . . . . . . . . . . .
💭Tili :</b>  $rew[tili]",
'parse_mode'=>"html",
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"🔹 Tomosha qilish 🔹",'url'=>"https://t.me/$bot?start=$text"]]
]
])
]);
sms($cid2,"<b>✅ Postingiz kanalga yuborildi!</b>",$panel);
exit();
}

if($text == "🔎 Foydalanuvchini boshqarish"){
if(in_array($cid,$admin)){
	bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Kerakli foydalanuvchining ID raqamini kiriting:</b>",
	'parse_mode'=>'html',
	'reply_markup'=>$boshqarish
	]);
file_put_contents("step/$cid.step",'iD');
exit();
}
}

if($step == "iD"){
if(in_array($cid,$admin)){
$result = mysqli_query($connect,"SELECT * FROM user_id WHERE user_id = '$text'");
$row = mysqli_fetch_assoc($result);
if(!$row){
bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Foydalanuvchi topilmadi.</b>

Qayta urinib ko'ring:",
'parse_mode'=>'html',
]);
exit();
}else{
$pul = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $text"))['pul'];
$odam = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $text"))['odam'];
$ban = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $text"))['ban'];
$status = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM status WHERE user_id = $text"))['status'];
if($status == "Oddiy"){
	$vip = "💎 VIP ga qo'shish";
}else{
	$vip = "❌ VIP dan olish";
}
if($ban == "unban"){
	$bans = "🔔 Banlash";
}else{
	$bans = "🔕 Bandan olish";
}
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Qidirilmoqda...</b>",
'parse_mode'=>'html',
]);
bot('editMessageText',[
        'chat_id'=>$cid,
        'message_id'=>$mid + 1,
        'text'=>"<b>Qidirilmoqda...</b>",
       'parse_mode'=>'html',
]);
bot('editMessageText',[
      'chat_id'=>$cid,
     'message_id'=>$mid + 1,
'text'=>"<b>Foydalanuvchi topildi!

ID:</b> <a href='tg://user?id=$text'>$text</a>
<b>Balans: $pul $valyuta
Takliflar: $odam ta</b>",
'parse_mode'=>'html',
'reply_markup'=>json_encode([
	'inline_keyboard'=>[
[['text'=>"$bans",'callback_data'=>"ban-$text"]],
[['text'=>"$vip",'callback_data'=>"addvip-$text"]],
[['text'=>"➕ Pul qo'shish",'callback_data'=>"plus-$text"],['text'=>"➖ Pul ayirish",'callback_data'=>"minus-$text"]]
]
])
]);
unlink("step/$cid.step");
exit();
}
}
}

if(mb_stripos($data, "foyda-")!==false){
$id = explode("-", $data)[1];
$pul = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $id"))['pul'];
$odam = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $id"))['odam'];
$ban = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $id"))['ban'];
$status = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM status WHERE user_id = $id"))['status'];
if($status == "Oddiy"){
	$vip = "💎 VIP ga qo'shish";
}else{
	$vip = "❌ VIP dan olish";
}
if($ban == "unban"){
	$bans = "🔔 Banlash";
}else{
	$bans = "🔕 Bandan olish";
}
bot('deleteMessage',[
'chat_id'=>$cid2,
'message_id'=>$mid2,
]);
bot('SendMessage',[
'chat_id'=>$cid2,
'text'=>"<b>Foydalanuvchi topildi!

ID:</b> <a href='tg://user?id=$id'>$id</a>
<b>Balans: $pul $valyuta
Takliflar: $odam ta</b>",
'parse_mode'=>'html',
'reply_markup'=>json_encode([
	'inline_keyboard'=>[
[['text'=>"$bans",'callback_data'=>"ban-$id"]],
[['text'=>"$vip",'callback_data'=>"addvip-$id"]],
[['text'=>"➕ Pul qo'shish",'callback_data'=>"plus-$id"],['text'=>"➖ Pul ayirish",'callback_data'=>"minus-$id"]]
]
])
]);
exit();
}

//<---- @AlijonovUz ---->//

if(mb_stripos($data, "plus-")!==false){
$id = explode("-", $data)[1];
bot('editMessageText',[
'chat_id'=>$cid2,
'message_id'=>$mid2,
'text'=>"<a href='tg://user?id=$id'>$id</a> <b>ning hisobiga qancha pul qo'shmoqchisiz?</b>",
'parse_mode'=>"html",
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
	[['text'=>"◀️ Orqaga",'callback_data'=>"foyda-$id"]]
]
])
]);
file_put_contents("step/$cid2.step","plus-$id");
}

if(mb_stripos($step, "plus-")!==false){
$id = explode("-", $step)[1];
if(in_array($cid,$admin)){
if(is_numeric($text)=="true"){
bot('sendMessage',[
'chat_id'=>$id,
'text'=>"<b>Adminlar tomonidan hisobingiz $text $valyuta to'ldirildi!</b>",
'parse_mode'=>"html",
]);
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Foydalanuvchi hisobiga $text $valyuta qo'shildi!</b>",
'parse_mode'=>"html",
'reply_markup'=>$panel,
]);
$pul = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $id"))['pul'];
$pul2 = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $id"))['pul2'];
$a = $pul + $text;
$b = $pul2 + $text;
mysqli_query($connect,"UPDATE kabinet SET pul = $a WHERE user_id = $id");
mysqli_query($connect,"UPDATE kabinet SET pul2 = $b WHERE user_id = $id");
if($cash == "Yoqilgan"){
$refid = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM user_id WHERE user_id = $id"))['refid'];
$pul3 = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $refid"))['pul'];
$c = $cashback / 100 * $text;
$jami = $pul3 + $c;
mysqli_query($connect,"UPDATE kabinet SET pul = $jami WHERE user_id = $refid");
}
bot('SendMessage',[
	'chat_id'=>$refid,
    'text'=>"💵 <b>Do'stingiz hisobini to'ldirganligi uchun sizga $cashback% cashback berildi!</b>",
	'parse_mode'=>'html',
]);
unlink("step/$cid.step");
exit();
}else{
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Faqat raqamlardan foydalaning!</b>",
'parse_mode'=>'html',
]);
exit();
}
}
}

if(mb_stripos($data, "minus-")!==false){
$id = explode("-", $data)[1];
bot('editMessageText',[
'chat_id'=>$cid2,
'message_id'=>$mid2,
'text'=>"<a href='tg://user?id=$id'>$id</a> <b>ning hisobiga qancha pul ayirmoqchisiz?</b>",
'parse_mode'=>"html",
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
	[['text'=>"◀️ Orqaga",'callback_data'=>"foyda-$id"]]
]
])
]);
file_put_contents("step/$cid2.step","minus-$id");
}

if(mb_stripos($step, "minus-")!==false){
$id = explode("-", $step)[1];
if(in_array($cid,$admin)){
if(is_numeric($text)=="true"){
bot('sendMessage',[
'chat_id'=>$id,
'text'=>"<b>Adminlar tomonidan hisobingizdan $text $valyuta olib tashlandi!</b>",
'parse_mode'=>"html",
]);
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Foydalanuvchi hisobidan $text $valyuta olib tashlandi!</b>",
'parse_mode'=>"html",
'reply_markup'=>$panel,
]);
$pul = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $id"))['pul'];
$a = $pul - $text;
mysqli_query($connect,"UPDATE kabinet SET pul = $a WHERE user_id = $id");
unlink("step/$cid.step");
exit();
}else{
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Faqat raqamlardan foydalaning!</b>",
'parse_mode'=>'html',
]);
exit();
}
}
}

if(mb_stripos($data, "ban-")!==false){
$id = explode("-", $data)[1];
$ban = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM kabinet WHERE user_id = $id"))['ban'];
if($obito_us != $id){
	if($ban == "ban"){
		$text = "<b>Foydalanuvchi ($id) bandan olindi!</b>";
		mysqli_query($connect,"UPDATE kabinet SET ban = 'unban' WHERE user_id = $id");
}else{
	$text = "<b>Foydalanuvchi ($id) banlandi!</b>";
	mysqli_query($connect,"UPDATE kabinet SET ban = 'ban' WHERE user_id = $id");
}
bot('editMessageText',[
'chat_id'=>$cid2,
'message_id'=>$mid2,
'text'=>$text,
'parse_mode'=>"html",
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
	[['text'=>"◀️ Orqaga",'callback_data'=>"foyda-$id"]]
]
])
]);
}else{
bot('answerCallbackQuery',[
'callback_query_id'=>$qid,
'text'=>"Asosiy adminlarni blocklash mumkin emas!",
'show_alert'=>true,
]);
}
}

if(mb_stripos($data, "addvip-")!==false){
$id = explode("-", $data)[1];
$status = mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM status WHERE user_id = $id"))['status'];
if($status == "VIP"){
	$text = "<b>Foydalanuvchi ($id) VIP dan olindi!</b>";
	mysqli_query($connect,"UPDATE status SET kun = '0' WHERE user_id = $id");
	mysqli_query($connect,"UPDATE status SET status = 'Oddiy' WHERE user_id = $id");
}else{
	$text = "<b>Foydalanuvchi ($id) VIP ga qo'shildi!</b>";
	mysqli_query($connect,"UPDATE status SET kun = '30' WHERE user_id = $id");
	mysqli_query($connect,"UPDATE status SET status = 'VIP' WHERE user_id = $id");
}
bot('editMessageText',[
'chat_id'=>$cid2,
'message_id'=>$mid2,
'text'=>$text,
'parse_mode'=>"html",
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
	[['text'=>"◀️ Orqaga",'callback_data'=>"foyda-$id"]]
]
])
]);
}

if($text == "✉ Xabar Yuborish" and in_array($cid,$admin)){
$result = mysqli_query($connect, "SELECT * FROM `send`");
$row = mysqli_fetch_assoc($result);
if(!$row){
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>📤 Foydalanuvchilarga yuboriladigan xabarni botga yuboring!</b>",
'parse_mode'=>'html',
'reply_markup'=>$aort
]);
put("step/$cid.step","send");
exit;
}else{
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>📑 Hozirda botda xabar yuborish jarayoni davom etmoqda. Yangi xabar yuborish uchun eski yuborilayotgan xabar barcha foydalanuvchilarga yuborilishini kuting!</b>",
'parse_mode'=>'html',
'reply_markup'=>$panel
]);
exit;
}
}

if($step== "send" and in_array($cid,$admin)){
$res = mysqli_query($connect,"SELECT * FROM `user_id` ORDER BY `id` DESC LIMIT 1");
$row = mysqli_fetch_assoc($res);
$user_id = $row['user_id'];
$time1 = date('H:i', strtotime('+1 minutes'));
$time2 = date('H:i', strtotime('+2 minutes'));
$tugma = json_encode($message->reply_markup);
$reply_markup = base64_encode($tugma);
mysqli_query($connect, "INSERT INTO `send` (`time1`,`time2`,`start_id`,`stop_id`,`admin_id`,`message_id`,`reply_markup`,`step`) VALUES ('$time1','$time2','0','$user_id','$cid','$mid','$reply_markup','send')");
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>📋 Saqlandi!
📑 Xabar foydalanuvchilarga $time1 da yuborish boshlanadi!</b>",
'parse_mode'=>'html',
'reply_markup'=>$panel
]);
unlink("step/$cid.step");
exit;
}

$result = mysqli_query($connect, "SELECT * FROM `send`"); 
$row = mysqli_fetch_assoc($result);
$sendstep = $row['step'];
$time = date('H:i');
if($_GET['update']=="send"){
$row1 = $row['time1'];
$row2 = $row['time2'];
$row3 = $row['time3'];
$row4 = $row['time4'];
$row5 = $row['time5'];
$start_id = $row['start_id'];
$stop_id = $row['stop_id'];
$admin_id = $row['admin_id'];
$mied = $row['message_id'];
$tugma = $row['reply_markup'];
if($tugma == "bnVsbA=="){
$reply_markup = "";
}else{
$reply_markup = base64_decode($tugma);
}
$time1 = date('H:i', strtotime('+1 minutes'));
$time2 = date('H:i', strtotime('+2 minutes'));
$time3 = date('H:i', strtotime('+3 minutes'));
$time4 = date('H:i', strtotime('+4 minutes'));
$time5 = date('H:i', strtotime('+5 minutes'));
$limit = 150;

if($time == $row1 or $time == $row2 or $time == $row3 or $time == $row4 or $time == $row5){
$sql = "SELECT * FROM `kabinet` LIMIT $start_id,$limit";
$res = mysqli_query($connect,$sql);
while($a = mysqli_fetch_assoc($res)){
$id = $a['user_id'];
$status = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM `status` WHERE `user_id` = $id"))['status'];
if($status == "Oddiy"){
if($id == $stop_id){
bot('copyMessage',[
'chat_id'=>$id,
'from_chat_id'=>$admin_id,
'message_id'=>$mied,
'disable_web_page_preview'=>true,
'reply_markup'=>$reply_markup
]);

bot('sendMessage',[
'chat_id'=>$admin_id,
'text'=>"<b>✅ Xabar barcha bot foydalanuvchilariga yuborildi!</b>",
'parse_mode'=>'html'
]);
mysqli_query($connect, "DELETE FROM `send`");
exit;
}else{
bot('copyMessage',[
'chat_id'=>$id,
'from_chat_id'=>$admin_id,
'message_id'=>$mied,
'disable_web_page_preview'=>true,
'reply_markup'=>$reply_markup
]);
}
}
}
mysqli_query($connect, "UPDATE `send` SET `time1` = '$time1'");
mysqli_query($connect, "UPDATE `send` SET `time2` = '$time2'");
mysqli_query($connect, "UPDATE `send` SET `time3` = '$time3'");
mysqli_query($connect, "UPDATE `send` SET `time4` = '$time4'");
mysqli_query($connect, "UPDATE `send` SET `time5` = '$time5'");
$get_id = $start_id + $limit;
mysqli_query($connect, "UPDATE `send` SET `start_id` = '$get_id'");
bot('sendMessage',[
'chat_id'=>$admin_id,
'text'=>"<b>✅ Yuborildi: $get_id</b>",
'parse_mode'=>'html'
]);
echo json_encode(["status"=>true,"cron"=>"Sending message"]);
}else{
echo json_encode(["status"=>false]);
}
}

// <---- @obito_us ---->

if($text == "📊 Statistika"){
if(in_array($cid,$admin)){
$res = mysqli_query($connect, "SELECT * FROM `user_id`");
$stat = mysqli_num_rows($res);
$ping = sys_getloadavg()[0];
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"💡 <b>O'rtacha yuklanish:</b> <code>$ping</code>

👥 <b>Foydalanuvchilar:</b> $stat ta",
'parse_mode'=>'html',
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"Orqaga",'callback_data'=>"boshqarish"]]
]
])
]);
exit();
}
}

// <---- @obito_us ---->

if($text == "📢 Kanallar"){
  if(in_array($cid,$admin)){
  bot('SendMessage',[
  'chat_id'=>$cid,
  'text'=>"<b>Quyidagilardan birini tanlang:</b>",
  'parse_mode'=>'html',
  'reply_markup'=>json_encode([
  'inline_keyboard'=>[
  [['text'=>"🔐 Majburiy obunalar",'callback_data'=>"majburiy"]],
  [['text'=>"📌 Qo'shimcha kanalar",'callback_data'=>"qoshimchakanal"]],
  ]
  ])
  ]);
  exit();
}
}

if($data == "kanallar"){
  bot('deleteMessage',[
  'chat_id'=>$cid2,
  'message_id'=>$mid2,
  ]);
  bot('SendMessage',[
  'chat_id'=>$cid2,
  'text'=>"<b>Quyidagilardan birini tanlang:</b>",
  'parse_mode'=>'html',
  'reply_markup'=>json_encode([
  'inline_keyboard'=>[
  [['text'=>"🔐 Majburiy obunalar",'callback_data'=>"majburiy"]],
  [['text'=>"📌 Qo'shimcha kanalar",'callback_data'=>"qoshimchakanal"]],
]
  ])
  ]);
  exit();
}



if($data == "qoshimchakanal"){  
    bot('editMessageText', [
        'chat_id'=>$cid2,
        'message_id'=>$mid2,
        'text'=>"<b>Qo'shimcha kanallar sozlash bo'limidasiz:</b>",
        'parse_mode'=>'html',
        'reply_markup'=>json_encode([
            'inline_keyboard'=>[
                [['text'=>"🎥 Anime kanal",'callback_data'=>"anime-kanal"]],
                [['text'=>"🧧 Link qo'shish", 'callback_data'=>"addlink"]],
                [['text'=>"🧧 Link ro'yxati", 'callback_data'=>"linklist"]],
                [['text'=>"🧧 Link O'chirish", 'callback_data'=>"dellink"]],
                [['text'=>"◀️ Orqaga",'callback_data'=>"kanallar"]]
            ]
        ])
    ]);
}

if ($data == "linklist" && in_array($cid, $admin)) {
    $links_file = "admin/links.json";
    if (file_exists($links_file)) {
        $links = json_decode(file_get_contents($links_file), true);
        if (is_array($links) && count($links) > 0) {
            $msg = "<b>📋 Linklar ro‘yxati:</b>\n\n";
            $i = 1;
            foreach ($links as $link) {
                $msg .= $i . ". <b>" . htmlspecialchars($link['name']) . "</b>\n";
                $msg .= "<code>" . htmlspecialchars($link['url']) . "</code>\n\n";
                $i++;
            }
            bot('sendMessage', [
                'chat_id' => $cid2,
                'text' => $msg,
                'parse_mode' => 'HTML',
                'disable_web_page_preview' => true
            ]);
        } else {
            bot('sendMessage', [
                'chat_id' => $cid2,
                'text' => "<b>❌ Hech qanday link qo‘shilmagan.</b>",
                'parse_mode' => 'HTML'
            ]);
        }
    } else {
        bot('sendMessage', [
            'chat_id' => $cid2,
            'text' => "<b>❌ Linklar ro‘yxati topilmadi.</b>",
            'parse_mode' => 'HTML'
        ]);
    }
}


if ($data == "dellink") {
    bot('deleteMessage', [
        'chat_id' => $cid2,
        'message_id' => $mid2,
    ]);

    // Avval barcha linklarni raqam bilan ko'rsatamiz
    $links_file = "admin/links.json";
    if (file_exists($links_file)) {
        $links = json_decode(file_get_contents($links_file), true);

        if (!empty($links)) {
            $list = "<b>📋 Linklar ro'yxati:</b>\n\n";
            foreach ($links as $index => $link) {
                $n = $index + 1;
                $list .= "$n. <b>{$link['name']}</b> — {$link['url']}\n";
            }
        } else {
            $list = "<b>📭 Linklar ro'yxati bo'sh!</b>\n\n";
        }
    } else {
        $list = "<b>📭 Linklar ro'yxati mavjud emas!</b>\n\n";
    }

    bot('SendMessage', [
        'chat_id' => $cid2,
        'text' => "$list\n<b>O‘chirish uchun link raqamini yuboring:</b>\n\nNamuna: <code>2</code>",
        'parse_mode' => 'html',
        'reply_markup' => $boshqarish,
    ]);

    file_put_contents("step/$cid2.step", "dellink");
    exit();
}

if ($step == "dellink" && in_array($cid, $admin)) {
    if (is_numeric($text)) {
        $links_file = "admin/links.json";
        if (file_exists($links_file)) {
            $links = json_decode(file_get_contents($links_file), true);
            $index = intval($text) - 1; // 1 dan boshlab keladi, array esa 0 dan

            if (isset($links[$index])) {
                $deleted = $links[$index]['name'];
                unset($links[$index]);

                // Qayta indekslaymiz
                $links = array_values($links);
                file_put_contents($links_file, json_encode($links, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

                bot('SendMessage', [
                    'chat_id' => $cid,
                    'text' => "<b>$deleted muvaffaqiyatli o‘chirildi.</b>",
                    'parse_mode' => 'html',
                    'reply_markup' => $panel,
                ]);
                unlink("step/$cid.step");
            } else {
                bot('SendMessage', [
                    'chat_id' => $cid,
                    'text' => "<b>Bunday raqamli link topilmadi!</b>\nQayta urinib ko‘ring.",
                    'parse_mode' => 'html',
                ]);
            }
        } else {
            bot('SendMessage', [
                'chat_id' => $cid,
                'text' => "<b>Linklar ro‘yxati mavjud emas.</b>",
                'parse_mode' => 'html',
            ]);
            unlink("step/$cid.step");
        }
    } else {
        bot('SendMessage', [
            'chat_id' => $cid,
            'text' => "<b>Iltimos, faqat raqam yuboring!</b>",
            'parse_mode' => 'html',
        ]);
    }
}


if ($data == "addlink") {
    del();
    bot('sendMessage', [
        'chat_id' => $cid2,
        'text' => "Link nomini kiriting (Masalan: Telegram):",
        'parse_mode' => "html",
    ]);
    file_put_contents("step/$cid2.step", "addlink_name");
}

if ($step == "addlink_name") {
    if (!empty($text)) {
        file_put_contents("step/$cid.step", "addlink_url|" . trim($text));
        bot('sendMessage', [
            'chat_id' => $cid,
            'text' => "Link manzilini yuboring (Masalan: https://t.me/username):",
            'parse_mode' => "html"
        ]);
    } else {
        bot('sendMessage', [
            'chat_id' => $cid,
            'text' => "Link nomini to‘g‘ri yuboring!",
            'parse_mode' => "html"
        ]);
    }
    exit();
}

if (strpos($step, "addlink_url|") === 0) {
    [$null, $link_name] = explode("|", $step, 2);
    if (!empty($text)) {
        $links_file = "admin/links.json";
        $links = file_exists($links_file) ? json_decode(file_get_contents($links_file), true) : [];

        $links[] = [
            "name" => $link_name,
            "url" => trim($text)
        ];

        file_put_contents($links_file, json_encode($links, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

        bot('sendMessage', [
            'chat_id' => $cid,
            'text' => "<b>$link_name</b> qo‘shildi ✅",
            'parse_mode' => 'HTML'
        ]);

        unlink("step/$cid.step");
    } else {
        bot('sendMessage', [
            'chat_id' => $cid,
            'text' => "Link manzilini yuboring!",
            'parse_mode' => 'HTML'
        ]);
    }
    exit();
}







if($data == "anime-kanal"){
  bot('deleteMessage',[
    'chat_id'=>$cid2,
    'message_id'=>$mid2,
    ]);
    bot('SendMessage',[
    'chat_id'=>$cid2,
  'text'=>"<i>Kanalingiz manzilini yuborishdan avval botni kanalingizga admin qilib olishingiz kerak!</i>
  
📢 <b>Kerakli kanalni manzilini yuboring:
  
Namuna:</b> <code>@username</code>",
  'parse_mode'=>'html',
  'reply_markup'=>$boshqarish,
  ]);
  file_put_contents("step/$cid2.step","anime-kanal");
  exit();
}

if($step == "anime-kanal"){
if(in_array($cid,$admin)){
if(isset($text)){    
if(mb_stripos($text, "@")!==false){
$get = bot('getChat',[
'chat_id'=>$text
]);
$types = $get->result->type;
$ch_name = $get->result->title;
$ch_user = $get->result->username;
if(getAdmin($ch_user)== true){
file_put_contents("admin/anime_kanal.txt",$text);
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>✅ Drama kanal $text.</b>",
'parse_mode'=>'html',
'reply_markup'=>$panel
]);
unlink("step/$cid.step");
exit();
}else{
bot('sendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Bot ushbu kanalda admin emas!</b>

Qayta urinib ko'ring:",
'parse_mode'=>'html',
]);
exit();
}
}else{
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Kanal manzilini to'g'ri yuboring:</b>
Namuna: <code>@username</code>",
'parse_mode'=>'html',
]);
exit();
}
}
}
}

if($data == "majburiy"){  
     bot('editMessageText',[
        'chat_id'=>$cid2,
       'message_id'=>$mid2,
'text'=>"<b>🔐Majburiy obunalarni sozlash bo'limidasiz:</b>",
'parse_mode'=>'html',
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"➕ Qo'shish",'callback_data'=>"qoshish"]],
[['text'=>"📑 Ro'yxat",'callback_data'=>"royxat"],['text'=>"🗑 O'chirish",'callback_data'=>"ochirish"]],
[['text'=>"🔙Ortga",'callback_data'=>"kanallar"]]
]
])
]);
}

if($data=="cancel" and in_array($cid2,$admin)){
del();
sms($cid2,"<b>✅Bekor qilindi !</b>",$panel);
}


if ($data == "qoshish") {
    del();
    sms($cid2, "<b>💬 Kanal ID sini yuboring!</b>", $boshqarish);
    file_put_contents("step/$cid2.step", "addchannel=id");
    exit();
}

if (stripos($step, "addchannel=") !== false && in_array($cid, $admin)) {
    $ty = str_replace("addchannel=", "", $step);

    // 1️⃣ Kanal ID kiritish bosqichi
    if ($ty == "id" && (is_numeric($text) || stripos($text, "-100") !== false)) {
        if (stripos($text, "-100") !== false) {
            $text = str_replace("-100", "", $text);
        }
        $text = "-100" . $text;
        file_put_contents("step/addchannel.txt", $text);
        sms($cid, "<b>📛 Kanal nomini kiriting!</b>", null);
        file_put_contents("step/$cid.step", "addchannel=name");
        exit();
    }

    // 2️⃣ Kanal nomi kiritish bosqichi
    elseif ($ty == "name") {
        file_put_contents("step/addchannelName.txt", $text);
        sms($cid, "<b>🔗 Kanal havolasini kiriting!</b>", null);
        file_put_contents("step/$cid.step", "addchannel=link");
        exit();
    }

    // 3️⃣ Kanal havolasini kiritish bosqichi
    elseif ($ty == "link") {
        if (stripos($text, "https://t.me/") !== false || stripos($text, "https://telegram.dog/") !== false || stripos($text, "https://telegram.me/") !== false) {
            file_put_contents("step/addchannelLink.txt", $text);
            
            // Kanal qo‘shildi, endi admin tasdiqlashini so‘raymiz
            sms($cid, "<b>⚠️ Ushbu kanal zayafka kanal sifatida qo‘shilsinmi?</b>", json_encode([
                'inline_keyboard' => [
                    [['text' => "✅ Ha", 'callback_data' => "addChannel=request"], ['text' => "❌ Yo‘q", 'callback_data' => "addChannel=lock"]],
                    [['text' => "🚫 Bekor qilish", 'callback_data' => "cancel"]]
                ]
            ]));

            file_put_contents("step/$cid.step", "addchannel=pending");
            exit();
        } else {
            sms($cid, "<b>📍 Faqat Telegram havolasi qabul qilinadi!</b>", null);
            exit();
        }
    }
}

// ✅ Callback bosilganda kanal ma'lumotlarini saqlaymiz va type ni yangilaymiz
if (stripos($data, "addChannel=") !== false && in_array($cid2, $admin)) {
    $ty = str_replace("addChannel=", '', $data);
    $channelId = file_get_contents("step/addchannel.txt");
    $channelName = file_get_contents("step/addchannelName.txt");
    $channelLink = file_get_contents("step/addchannelLink.txt");

    if ($ty == "request" || $ty == "lock") {
        // Ma'lumotlar bazasiga ulanish
        if ($connect->connect_error) {
            sms($cid2, "<b>❌ Ma'lumotlar bazasiga ulanishda xatolik!</b>", null);
            exit();
        }

        // Ma'lumotlarni saqlash
        $stmt = $connect->prepare("INSERT INTO channels (channelId, nom, channelLink, channelType) VALUES (?, ?, ?, ?)");
        if (!$stmt) {
            sms($cid2, "<b>❌ So'rov tayyorlashda xatolik: " . $connect->error . "</b>", null);
            exit();
        }

        $stmt->bind_param("ssss", $channelId, $channelName, $channelLink, $ty);

        if (!$stmt->execute()) {
            sms($cid2, "<b>❌ Ma'lumotni saqlashda xatolik: " . $stmt->error . "</b>", null);
            exit();
        }
        $stmt->close();

        // Muvaffaqiyatli xabar
        del();
        sms($cid2, "<b>✅ Majburiy obunaga kanal ulandi!</b>", $panel);
        
        // Vaqtinchalik fayllarni o'chirish
        @unlink("step/$cid2.step");
        @unlink("step/addchannel.txt");
        @unlink("step/addchannelName.txt");
        @unlink("step/addchannelLink.txt");
    } elseif ($ty == "cancel") {
        del();
        sms($cid2, "<b>🚫 Kanal qo‘shish bekor qilindi!</b>", $panel);
        @unlink("step/$cid2.step");
        @unlink("step/addchannel.txt");
        @unlink("step/addchannelName.txt");
        @unlink("step/addchannelLink.txt");
    } else {
        accl($qid, "⚠️ Tizimda xatolik!", 1);
    }
}



if($data == "ochirish"){
$query=$connect->query("SELECT * FROM `channels`");
if($query->num_rows>0){
$soni=$query->num_rows;
$text="<b>✂️Kanalni uzish uchun kanal raqami ustiga bosing !</b>\n";
$co=1;
while($row=$query->fetch_assoc()){
$text .="\n<b>$co.</b> ".$row['channelLink']." | ".$row['channelType'];
$uz[]=['text'=>"🗑".$co,'callback_data'=>"channelDelete=".$row['id']];
$co++;
}
$e=array_chunk($uz,5);
$e[]=[['text'=>"🔙Ortga",'callback_data'=>"majburiy"]];
$json=json_encode(['inline_keyboard'=>$e]);
$text .= "\n\n<b>Ulangan kanallar soni:</b> $soni ta";
edit($cid2,$mid2,$text,$json);
}else accl($qid,"Hech qanday kanallar ulanmagan!",1);
}

if(stripos($data,"channelDelete=")!==false and in_array($cid2,$admin)){
$ty=str_replace("channelDelete=",'',$data);
$sql = "DELETE FROM `channels` WHERE `id` = '$ty'";
if($connect->query($sql)){
accl($qid,"Kanal uzildi✔️");
$query=$connect->query("SELECT * FROM `channels`");
if($query->num_rows>0){
$soni=$query->num_rows;
$text="<b>✂️Kanalni uzish uchun kanal raqami ustiga bosing !</b>\n";
$co=1;
$uz=[];
while($row=$query->fetch_assoc()){
$text .="\n<b>$co.</b> ".$row['channelLink']." | ".$row['channelType'];
$uz[]=['text'=>"🗑".$co,'callback_data'=>"channelDelete=".$row['id']];
$co++;
}
$e=array_chunk($uz,5);
$e[]=[['text'=>"🔙Ortga",'callback_data'=>"majburiy"]];
$json=json_encode(['inline_keyboard'=>$e]);
$text .= "\n\n<b>Ulangan kanallar soni:</b> $soni ta";
edit($cid2,$mid2,$text,$json);
}else{
del();
sms($cid2,"<b>☑️Majburiy obuna ulangan kanallar qolmadi !</b>",$panel);
}
}else accl($qid,"⚠️Tizimda xatolik!\n\n".$connect->error,1);
}

if($data == "royxat"){
$query=$connect->query("SELECT * FROM `channels`");
if($query->num_rows>0){
$soni=$query->num_rows;
$text="<b>📢 Kanallar ro'yxati:</b>\n";
$co=1;
while($row=$query->fetch_assoc()){
$text .="\n<b>$co.</b> ".$row['channelLink']." | ".$row['channelType'];
}
$text .= "\n\n<b>Ulangan kanallar soni:</b> $soni ta";
edit($cid2,$mid2,$text,json_encode([
'inline_keyboard'=>[
[['text'=>"🔙Ortga",'callback_data'=>"majburiy"]],
]]));
}else accl($qid,"Hech qanday kanallar ulanmagan!",1);
}

// <---- @obito_us ---->

if($text == "📋 Adminlar"){
if(in_array($cid,$admin)){
	if($cid == $obito_us){
	bot('SendMessage',[
	'chat_id'=>$obito_us,
	'text'=>"<b>Quyidagilardan birini tanlang:</b>",
	'parse_mode'=>'html',
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
   [['text'=>"➕ Yangi admin qo'shish",'callback_data'=>"add"]],
   [['text'=>"📑 Ro'yxat",'callback_data'=>"list"],['text'=>"🗑 O'chirish",'callback_data'=>"remove"]],
	[['text'=>"Orqaga",'callback_data'=>"boshqarish"]]
	]
	])
	]);
	exit();
}else{	
bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Quyidagilardan birini tanlang:</b>",
	'parse_mode'=>'html',
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
   [['text'=>"📑 Ro'yxat",'callback_data'=>"list"]],
[['text'=>"Orqaga",'callback_data'=>"boshqarish"]]
	]
	])
	]);
	exit();
}
}
}

if($data == "admins"){
if($cid2 == $obito_us){
	bot('deleteMessage',[
	'chat_id'=>$cid2,
	'message_id'=>$mid2,
	]);	
bot('SendMessage',[
	'chat_id'=>$obito_us,
	'text'=>"<b>Quyidagilardan birini tanlang:</b>",
	'parse_mode'=>'html',
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
   [['text'=>"➕ Yangi admin qo'shish",'callback_data'=>"add"]],
   [['text'=>"📑 Ro'yxat",'callback_data'=>"list"],['text'=>"🗑 O'chirish",'callback_data'=>"remove"]],
	[['text'=>"Orqaga",'callback_data'=>"boshqarish"]]
	]
	])
	]);
	exit();
}else{
bot('deleteMessage',[
	'chat_id'=>$cid2,
	'message_id'=>$mid2,
	]);	
bot('SendMessage',[
	'chat_id'=>$cid2,
	'text'=>"<b>Quyidagilardan birini tanlang:</b>",
	'parse_mode'=>'html',
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
   [['text'=>"📑 Ro'yxat",'callback_data'=>"list"]],
[['text'=>"Orqaga",'callback_data'=>"boshqarish"]]
	]
	])
	]);
	exit();
}
}

if($data == "list"){
$add = str_replace($obito_us,"",$admins);
if($admins == $obito_us){
	$text = "<b>Yordamchi adminlar topilmadi!</b>";
}else{
		$text = "<b>👮 Adminlar ro'yxati:</b>
$add";
}
     bot('editMessageText',[
        'chat_id'=>$cid2,
       'message_id'=>$mid2,
       'text'=>$text,
'parse_mode'=>'html',
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"Orqaga",'callback_data'=>"admins"]],
]
])
]);
}

if($data == "add"){
bot('deleteMessage',[
'chat_id'=>$cid2,
'message_id'=>$mid2,
]);
bot('SendMessage',[
'chat_id'=>$obito_us,
'text'=>"<b>Kerakli foydalanuvchi ID raqamini yuboring:</b>",
'parse_mode'=>'html',
'reply_markup'=>$boshqarish
]);
file_put_contents("step/$cid2.step",'add-admin');
exit();
}
if($step == "add-admin" and $cid == $obito_us){
$result = mysqli_query($connect,"SELECT * FROM user_id WHERE user_id = '$text'");
$row = mysqli_fetch_assoc($result);
if(!$row){
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Ushbu foydalanuvchi botdan foydalanmaydi!</b>

Boshqa ID raqamni kiriting:",
'parse_mode'=>'html',
]);
exit();
}elseif((mb_stripos($admins, $text)!==false) or ($text != $obito_us)){
file_put_contents("admin/admins.txt","\n".$text,FILE_APPEND);
bot('SendMessage',[
'chat_id'=>$obito_us,
'text'=>"<code>$text</code> <b>adminlar ro'yxatiga qo'shildi!</b>",
'parse_mode'=>'html',
'reply_markup'=>$panel
]);
unlink("step/$cid.step");
exit();
}else{
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Ushbu foydalanuvchi adminlari ro'yxatida mavjud!</b>

Boshqa ID raqamni kiriting:",
'parse_mode'=>'html',
]);
exit();
}
}

if($data == "remove"){
bot('deleteMessage',[
'chat_id'=>$cid2,
'message_id'=>$mid2,
]);
bot('SendMessage',[
'chat_id'=>$obito_us,
'text'=>"<b>Kerakli foydalanuvchi ID raqamini yuboring:</b>",
'parse_mode'=>'html',
'reply_markup'=>$boshqarish
]);
file_put_contents("step/$cid2.step",'remove-admin');
exit();
}
if($step == "remove-admin" and $cid == $obito_us){
$result = mysqli_query($connect,"SELECT * FROM user_id WHERE user_id = '$text'");
$row = mysqli_fetch_assoc($result);
if(!$row){
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Ushbu foydalanuvchi botdan foydalanmaydi!</b>

Boshqa ID raqamni kiriting:",
'parse_mode'=>'html',
]);
exit();
}elseif((mb_stripos($admins, $text)!==false) or ($text != $obito_us)){
$files = file_get_contents("admin/admins.txt");
$file = str_replace("\n".$text."","",$files);
file_put_contents("admin/admins.txt",$file);
bot('SendMessage',[
'chat_id'=>$obito_us,
'text'=>"<code>$text</code> <b>adminlar ro'yxatidan olib tashlandi!</b>",
'parse_mode'=>'html',
'reply_markup'=>$panel
]);
unlink("step/$cid.step");
exit();
}else{
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Ushbu foydalanuvchi adminlari ro'yxatida mavjud emas!</b>

Boshqa ID raqamni kiriting:",
'parse_mode'=>'html',
]);
exit();
}
}

//<---- @AlijonovUz ---->//

if($text == "🤖 Bot holati"){
	if(in_array($cid,$admin)){
	if($holat == "Yoqilgan"){
		$xolat = "O'chirish";
	}
	if($holat == "O'chirilgan"){
		$xolat = "Yoqish";
	}
	bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Hozirgi holat:</b> $holat",
	'parse_mode'=>'html',
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
[['text'=>"$xolat",'callback_data'=>"bot"]],
[['text'=>"Orqaga",'callback_data'=>"boshqarish"]]
]
])
]);
exit();
}
}

if($data == "xolat"){
	if($holat == "Yoqilgan"){
		$xolat = "O'chirish";
	}
	if($holat == "O'chirilgan"){
		$xolat = "Yoqish";
	}
	bot('deleteMessage',[
	'chat_id'=>$cid2,
	'message_id'=>$mid2,
	]);
	bot('SendMessage',[
	'chat_id'=>$cid2,
	'text'=>"<b>Hozirgi holat:</b> $holat",
	'parse_mode'=>'html',
	'reply_markup'=>json_encode([
	'inline_keyboard'=>[
[['text'=>"$xolat",'callback_data'=>"bot"]],
[['text'=>"Orqaga",'callback_data'=>"boshqarish"]]
]
])
]);
exit();
}

if($data == "bot"){
if($holat == "Yoqilgan"){
file_put_contents("admin/holat.txt","O'chirilgan");
     bot('editMessageText',[
        'chat_id'=>$cid2,
       'message_id'=>$mid2,
       'text'=>"<b>Muvaffaqiyatli o'zgartirildi!</b>",
'parse_mode'=>'html',
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"◀️ Orqaga",'callback_data'=>"xolat"]],
]
])
]);
}else{
file_put_contents("admin/holat.txt","Yoqilgan");
     bot('editMessageText',[
        'chat_id'=>$cid2,
       'message_id'=>$mid2,
       'text'=>"<b>Muvaffaqiyatli o'zgartirildi!</b>",
'parse_mode'=>'html',
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"◀️ Orqaga",'callback_data'=>"xolat"]],
]
])
]);
}
}

//<---- @AlijonovUz ---->//

if($text == "⚙ Asosiy sozlamalar"){
		if(in_array($cid,$admin)){
	bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Asosiy sozlamalar bo'limidasiz.</b>",
	'parse_mode'=>'html',
	'reply_markup'=>$asosiy,
	]);
	exit();
}
}

$delturi = file_get_contents("tizim/turi.txt");
$delmore = explode("\n",$delturi);
$delsoni = substr_count($delturi,"\n");
$key=[];
for ($delfor = 1; $delfor <= $delsoni; $delfor++) {
$title=str_replace("\n","",$delmore[$delfor]);
$key[]=["text"=>"$title - ni o'chirish","callback_data"=>"del-$title"];
$keyboard2 = array_chunk($key, 1);
$keyboard2[] = [['text'=>"➕ Yangi to'lov tizimi qo'shish",'callback_data'=>"new"]];
$pay = json_encode([
'inline_keyboard'=>$keyboard2,
]);
}

if($text == "💳 Hamyonlar"){
		if(in_array($cid,$admin)){
if($turi == null){
bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Quyidagilardan birini tanlang:</b>",
	'parse_mode'=>'html',
		'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"➕ Yangi to'lov tizimi qo'shish",'callback_data'=>"new"]],
]
])
]);
exit();
}else{
	bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Quyidagilardan birini tanlang:</b>",
	'parse_mode'=>'html',
		'reply_markup'=>$pay
]);
exit();
}
}
}

if($data == "hamyon"){
if($turi == null){
bot('deleteMessage',[
	'chat_id'=>$cid2,
	'message_id'=>$mid2,
	]);
bot('SendMessage',[
	'chat_id'=>$cid2,
	'text'=>"<b>Quyidagilardan birini tanlang:</b>",
	'parse_mode'=>'html',
		'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"➕ Yangi to'lov tizimi qo'shish",'callback_data'=>"new"]],
]
])
]);
exit();
}else{
	bot('deleteMessage',[
	'chat_id'=>$cid2,
	'message_id'=>$mid2,
	]);
bot('SendMessage',[
	'chat_id'=>$cid2,
	'text'=>"<b>Quyidagilardan birini tanlang:</b>",
	'parse_mode'=>'html',
		'reply_markup'=>$pay
]);
exit();
}
}

//<---- @AlijonovUz ---->//

if(mb_stripos($data,"del-")!==false){
	$ex = explode("-",$data);
	$tur = $ex[1];
	$k = str_replace("\n".$tur."","",$turi);
   file_put_contents("tizim/turi.txt",$k);
bot('deleteMessage',[
	'chat_id'=>$cid2,
	'message_id'=>$mid2,
	]);
bot('SendMessage',[
	'chat_id'=>$cid2,
	'text'=>"<b>To'lov tizimi o'chirildi!</b>",
		'parse_mode'=>'html',
	'reply_markup'=>$asosiy
]);
deleteFolder("tizim/$tur");
}

	/*$test = file_get_contents("step/test.txt");
   $k = str_replace("\n".$test."","",$turi);
   file_put_contents("tizim/turi.txt",$k);
deleteFolder("tizim/$test");
unlink("step/test.txt");
exit();*/

if($data == "new"){
	bot('deleteMessage',[
	'chat_id'=>$cid2,
	'message_id'=>$mid2,
   ]);
   bot('sendMessage',[
   'chat_id'=>$cid2,
   'text'=>"<b>Yangi to'lov tizimi nomini yuboring:</b>",
   'parse_mode'=>'html',
   'reply_markup'=>$boshqarish
	]);
	file_put_contents("step/$cid2.step",'turi');
	exit();
}

if($step == "turi"){
if(in_array($cid,$admin)){
if(isset($text)){
mkdir("tizim/$text");
file_put_contents("tizim/turi.txt","$turi\n$text");
	file_put_contents("step/test.txt",$text);
	bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Ushbu to'lov tizimidagi hamyoningiz raqamini yuboring:</b>",
	'parse_mode'=>'html',
	]);
	file_put_contents("step/$cid.step",'wallet');
	exit();
}
}
}


if($step == "wallet"){
if(in_array($cid,$admin)){
if(is_numeric($text)=="true"){
file_put_contents("tizim/$test/wallet.txt","$wallet\n$text");
	bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Ushbu to'lov tizimi orqali hisobni to'ldirish bo'yicha ma'lumotni yuboring:</b>

<i>Misol uchun, \"Ushbu to'lov tizimi orqali pul yuborish jarayonida izoh kirita olmasligingiz mumkin. Ushbu holatda, biz bilan bog'laning. Havola: @AlijonovUz</i>\"",
'parse_mode'=>'html',
	]);
	file_put_contents("step/$cid.step",'addition');
	exit();
}else{
bot('SendMessage',[
'chat_id'=>$cid,
'text'=>"<b>Faqat raqamlardan foydalaning!</b>",
'parse_mode'=>'html',
]);
exit();
}
}
}

if($step == "addition"){
		if(in_array($cid,$admin)){
	if(isset($text)){
file_put_contents("tizim/$test/addition.txt","$addition\n$text");
	bot('SendMessage',[
	'chat_id'=>$cid,
	'text'=>"<b>Yangi to'lov tizimi qo'shildi!</b>",
	'parse_mode'=>'html',
	'reply_markup'=>$asosiy,
	]);
	unlink("step/$cid.step");
	unlink("step/test.txt");
	exit();
}
}
}

// <---- @obito_us ---->

if($text == "🎥 Animelar sozlash" and in_array($cid,$admin)){
sms($cid,"<b>Quyidagilardan birini tanlang:</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"➕ Anime qo'shish",'callback_data'=>"add-anime"]],
[['text'=>"📥 Qism qo'shish",'callback_data'=>"add-episode"]],
[['text'=>"📝 Anime tahrirlash",'callback_data'=>"edit-anime"]],
]]));
exit();
}

if($data == "add-anime"){
del();
sms($cid2,"<b>🍿 Anime nomini kiriting:</b>",$boshqarish);
put("step/$cid2.step","anime-name");
}

if($step == "anime-name" and in_array($cid,$admin)){
if(isset($text)){
if(containsEmoji($text)==false){
$text = $connect->real_escape_string($text);
put("step/test.txt",$text);
sms($cid,"<b>🎥 Jami qismlar sonini kiriting:</b>",$boshqarish);
put("step/$cid.step","anime-episodes");
exit();
}else{
sms($cid,"<b>⚠️ Anime qo'shishda emoji va shunga o'xshash maxsus belgilardan foydalanish taqiqlangan!</b>

Qayta urining",null);
}
}
}

if($step == "anime-episodes" and in_array($cid,$admin)){
if(isset($text)){
$text = $connect->real_escape_string($text);
put("step/test2.txt",$text);
sms($cid,"<b>🌍 Qaysi davlat ishlab chiqarganini kiriting:</b>",$boshqarish);
put("step/$cid.step","anime-country");
exit();
}
}

if($step == "anime-country" and in_array($cid,$admin)){
if(isset($text)){
$text = $connect->real_escape_string($text);
put("step/test3.txt",$text);
sms($cid,"<b>🇺🇿 Qaysi tilda ekanligini kiriting:</b>",$boshqarish);
put("step/$cid.step","anime-language");
exit();
}
}

if($step == "anime-language" and in_array($cid,$admin)){
if(isset($text)){
$text = $connect->real_escape_string($text);
put("step/test4.txt",$text);
sms($cid,"<b>📆 Qaysi yilda ishlab chiqarilganini kiriting:</b>",$boshqarish);
put("step/$cid.step","anime-year");
exit();
}
}

if($step == "anime-year" and in_array($cid,$admin)){
if(isset($text)){
$text = $connect->real_escape_string($text);
put("step/test5.txt",$text);
sms($cid,"<b>🎞 Janrlarini kiriting:</b>

<i>Na'muna: Drama, Fantastika, Sarguzash</i>",$boshqarish);
put("step/$cid.step","anime-genre");
exit();
}
}

if($step == "anime-genre" and in_array($cid,$admin)){
if(isset($text)){
$text = $connect->real_escape_string($text);
put("step/test6.txt",$text);
sms($cid,"<b>🏞 Rasmini yuboring:</b>",$boshqarish);
put("step/$cid.step","anime-picture");
exit();
}
}

if($step == "anime-picture" and in_array($cid,$admin)){
if(isset($message->photo)){
$file_id = $message->photo[count($message->photo)-1]->file_id;
$nom = get("step/test.txt");
$qismi = get("step/test2.txt");
$davlati = get("step/test3.txt");
$tili = get("step/test4.txt");
$yili = get("step/test5.txt");
$janri = get("step/test6.txt");
$date = date('H:i d.m.Y');
if($connect->query("INSERT INTO `animelar` (`nom`, `rams`, `qismi`, `davlat`, `tili`, `yili`, `janri`, `qidiruv`, `sana`) VALUES ('$nom', '$file_id', '$qismi', '$davlati', '$tili', '$yili', '$janri', '0', '$date')")==TRUE){
$code = $connect->insert_id;
sms($cid,"<b>✅ Anime qo'shildi!</b>

<b>Anime kodi:</b> <code>$code</code>",$panel);
unlink("step/$cid.step");
unlink("step/test.txt");
unlink("step/test2.txt");
unlink("step/test3.txt");
unlink("step/test4.txt");
unlink("step/test5.txt");
unlink("step/test6.txt");
exit();
}else{
sms($cid,"<b>⚠️ Xatolik!</b>\n\n<code>$connect->error</code>",$panel);
unlink("step/$cid.step");
unlink("step/test.txt");
unlink("step/test2.txt");
unlink("step/test3.txt");
unlink("step/test4.txt");
unlink("step/test5.txt");
unlink("step/test6.txt");
exit();
}
}
}

if($data == "add-episode"){
del();
sms($cid2,"<b>🔢 Anime kodini kiriting:</b>",$boshqarish);
put("step/$cid2.step","episode-code");
}

if($step == "episode-code" and in_array($cid,$admin)){
if(is_numeric($text)){
$text = $connect->real_escape_string($text);
put("step/test.txt",$text);
sms($cid,"<b>🎥 Ushbu kodga tegishlik anime qismini yuboring:</b>",$boshqarish);
put("step/$cid.step","episode-video");
exit();
}
}

if($step == "episode-video" and in_array($cid,$admin)){
if(isset($message->video)){
$file_id = $message->video->file_id;
$id = get("step/test.txt");
$qism = $connect->query("SELECT * FROM anime_datas WHERE id = $id")->num_rows;
$qismi = $qism+1;
$sana = date('H:i:s d.m.Y');
if($connect->query("INSERT INTO anime_datas(id,file_id,qism,sana) VALUES ('$id','$file_id','$qismi','$sana')")==TRUE){
$code = $connect->insert_id;
sms($cid,"<b>✅ $id raqamli animega $qismi-qism yuklandi!</b>

<i>Yana yuklash uchun keyingi qismni yuborsangiz bo'ldi</i>",null);
exit();
}else{
sms($cid,"<b>⚠️ Xatolik!</b>\n\n<code>$connect->error</code>",$panel);
unlink("step/$cid.step");
unlink("step/test.txt");
unlink("step/test2.txt");
exit();
}
}
}

if($data=="edit-anime"){
edit($cid2,$mid2,"<b>Tahrirlamoqchi bo'lgan animeni tanlang:</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"Anime ma'lumotlarini",'callback_data'=>"editType-animes"]],
[['text'=>"Anime qismini",'callback_data'=>"editType-anime_datas"]]
]]));
}

if(mb_stripos($data,"editType-")!==false){
$ex = explode("-",$data)[1];
put("step/$cid2.tip",$ex);
del();
sms($cid2,"<b>Anime kodini kiriting:</b>",$boshqarish);
put("step/$cid2.step","edit-anime");
}

if($step == "edit-anime"){
$tip=get("step/$cid.tip");
if($tip=="animes"){
$result=mysqli_query($connect,"SELECT * FROM animelar WHERE id = $text");
$row=mysqli_fetch_assoc($result);
if($row){
$kb=json_encode([
'inline_keyboard'=>[
[['text'=>"Nomini tahrirlash",'callback_data'=>"editAnime-nom-$text"]],
[['text'=>"Qismini tahrirlash",'callback_data'=>"editAnime-qismi-$text"]],
[['text'=>"Davlatini tahrirlash",'callback_data'=>"editAnime-davlat-$text"]],
[['text'=>"Tilini tahrirlash",'callback_data'=>"editAnime-tili-$text"]],
[['text'=>"Yilini tahrirlash",'callback_data'=>"editAnime-yili-$text"]],
[['text'=>"Janrini tahrirlash",'callback_data'=>"editAnime-janri-$text"]],
]]);
sms($cid,"<b>❓ Nimani tahrirlamoqchisiz?</b>",$kb);
unlink("step/$cid2.step");
exit();
}else{
sms($cid,"<b>❗ Anime mavjud emas, qayta urinib ko'ring!</b>",null);
exit();
}
}else{
$result=mysqli_query($connect,"SELECT * FROM animelar WHERE id = $text");
$row=mysqli_fetch_assoc($result);
if($row){
sms($cid,"<b>Qism raqamini yuboring:</b>",$boshqarish);
put("step/$cid.step","anime-epEdit=$text");
exit();
}else{
sms($cid,"<b>❗ Anime mavjud emas, qayta urinib ko'ring!</b>",null);
exit();
}
}
}

if(mb_stripos($step,"anime-epEdit=")!==false){
$ex = explode("=",$step);
$id = $ex[1];
$result=mysqli_query($connect,"SELECT * FROM anime_datas WHERE id = $id AND qism = $text");
$row=mysqli_fetch_assoc($result);
if($row){
$kb=json_encode([
'inline_keyboard'=>[
[['text'=>"Anime kodini tahrirlash",'callback_data'=>"editEpisode-id-$id-$text"]],
[['text'=>"Qismini tahrirlash",'callback_data'=>"editEpisode-qism-$id-$text"]],
[['text'=>"Videoni tahrirlash",'callback_data'=>"editEpisode-file_id-$id-$text"]],
]]);
sms($cid,"<b>❓ Nimani tahrirlamoqchisiz?</b>",$kb);
unlink("step/$cid.step");
exit();
}else{
sms($cid,"<b>❗ Ushbu animeda $text-qism mavjud emas, qayta urinib ko'ring.</b>",null);
exit();
}
}

if(mb_stripos($data,"editAnime-")!==false){
del();
sms($cid2,"<b>Yangi qiymatini kiriting:</b>",$boshqarish);
put("step/$cid2.step",$data);
}

if(mb_stripos($step,"editAnime-")!==false){
$ex = explode("-",$step);
$tip = $ex[1];
$id = $ex[2];
if($tip=="qismi" and $tip=="yili"){
if(is_numeric($text)){
mysqli_query($connect,"UPDATE animes SET `$tip`='$text' WHERE id = $id");
sms($cid,"<b>✅ Saqlandi.</b>",null);
unlink("step/$cid.step");
exit();
}else{
sms($cid,"<b>❗Faqat raqamlardan foydalaning.</b>",null);
exit();
}
}else{
if(isset($text)){
mysqli_query($connect,"UPDATE animes SET `$tip`='$text' WHERE id = $id");
sms($cid,"<b>✅ Saqlandi.</b>",null);
unlink("step/$cid.step");
exit();
}else{
sms($cid,"<b>❗Faqat matnlardan foydalaning.</b>",null);
exit();
}
}
}

if(mb_stripos($data,"editEpisode-")!==false){
del();
sms($cid2,"<b>Yangi qiymatini kiriting:</b>",$boshqarish);
put("step/$cid2.step",$data);
}

if(mb_stripos($step,"editEpisode-")!==false){
$ex = explode("-",$step);
$tip = $ex[1];
$id = $ex[2];
$qism_raqami = $ex[3];
if($tip=="file_id"){
if(isset($message->video)){
$file_id = $message->video->file_id;
mysqli_query($connect,"UPDATE anime_datas SET `file_id`='$file_id' WHERE id = $id AND qism = $qism_raqami");
sms($cid,"<b>✅ Saqlandi.</b>",null);
unlink("step/$cid.step");
exit();
}else{
sms($cid,"<b>❗Faqat videodan foydalaning.</b>",null);
exit();
}
}else{
if(is_numeric($text)){
mysqli_query($connect,"UPDATE anime_datas SET `$tip`='$text' WHERE id = $id AND qism = $qism_raqami");
sms($cid,"<b>✅ Saqlandi.</b>",null);
unlink("step/$cid.step");
exit();
}else{
sms($cid,"<b>❗Faqat raqamlardan foydalaning.</b>",null);
exit();
}
}
}

// <---- @obito_us ---->

if($text == "*️⃣ Birlamchi sozlamalar"){
if(in_array($cid,$admin)){
sms($cid,"<b>Hozirgi birlamchi sozlamalar:</b>

<i>1. Valyuta - $valyuta
2. VIP narxi - $narx $valyuta
3. Studiya nomi - $studio_name</i>",json_encode([
'inline_keyboard'=>[
[['text'=>"1",'callback_data'=>"valyuta"],['text'=>"2",'callback_data'=>"vnarx"],['text'=>"3",'callback_data'=>"studio_name"]],
]]));
exit();
}
}

if($data == "birlamchi"){
edit($cid2,$mid2,"<b>Hozirgi birlamchi sozlamalar:</b>

<i>1. Valyuta - $valyuta
2. VIP narxi - $narx $valyuta</i>",json_encode([
'inline_keyboard'=>[
[['text'=>"1",'callback_data'=>"valyuta"],['text'=>"2",'callback_data'=>"vnarx"]],
]]));
exit();
}

if($data == "valyuta"){
del();
sms($cid2,"📝 <b>Yangi qiymatni yuboring:</b>",$boshqarish);
put("step/$cid2.step",'valyuta');
exit();
}

if($step == "valyuta" and in_array($cid,$admin)){
if(isset($text)){
put("admin/vip.txt",$text);
sms($cid,"<b>✅ Saqlandi.</b>",$panel);
unlink("step/$cid.step");
exit();
}
}

if($data == "vnarx"){
del();
sms($cid2,"📝 <b>Yangi qiymatni yuboring:</b>",$boshqarish);
put("step/$cid2.step",'vnarx');
exit();
}

if($step == "vnarx" and in_array($cid,$admin)){
if(isset($text)){
put("admin/vip.txt",$text);
sms($cid,"<b>✅ Saqlandi.</b>",$panel);
unlink("step/$cid.step");
exit();
}
}

if($data == "studio_name"){
del();
sms($cid2,"📝 <b>Yangi qiymatni yuboring:</b>",$boshqarish);
put("step/$cid2.step",'vnarx');
exit();
}

if($step == "studio_name" and in_array($cid,$admin)){
if(isset($text)){
put("admin/studio_name.txt",$text);
sms($cid,"<b>✅ Saqlandi.</b>",$panel);
unlink("step/$cid.step");
exit();
}
}

// <---- @obito_us ---->

if($text == "📃 Matnlar" and in_array($cid,$admin)){
sms($cid,"<b>Quyidagilardan birini tanlang:</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"Boshlang'ich matni",'callback_data'=>"matn1"]],
[['text'=>"Qo'llanma",'callback_data'=>"matn2"]],
[['text'=>"🔖 Homiy matni",'callback_data'=>"matn5"]],
]]));
exit();
}

if($data == "matn1"){
del();
sms($cid2,"<b>Boshlang'ich matnini yuboring:</b>",$boshqarish);
put("step/$cid2.step",'matn1');
exit();
}

if($step == "matn1" and in_array($cid,$admin)){
if(isset($text)){
put("matn/start.txt",$text);
sms($cid,"<b>✅ Saqlandi.</b>",$panel);
unlink("step/$cid.step");
exit();
}
}

if($data == "matn2"){
del();
sms($cid2,"<b>Qo'llanma matnini yuboring::</b>",$boshqarish);
put("step/$cid2.step",'matn2');
exit();
}

if($step == "matn2" and in_array($cid,$admin)){
if(isset($text)){
put("matn/qollanma.txt",$text);
sms($cid,"<b>✅ Saqlandi.</b>",$panel);
unlink("step/$cid.step");
exit();
}
}

if($data == "matn5"){
del();
sms($cid2,"<b>Homiy matnini yuboring:</b>",$boshqarish);
put("step/$cid2.step",'matn5');
exit();
}

if($step == "matn5" and in_array($cid,$admin)){
if(isset($text)){
put("matn/homiy.txt",$text);
sms($cid,"<b>✅ Saqlandi.</b>",$panel);
unlink("step/$cid.step");
exit();
}
}

// <---- @obito_us ---->

if($text == "🎛 Tugmalar" and in_array($cid,$admin)){
sms($cid,"<b>Quyidagilardan birini tanlang:</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"🖥 Asosiy menyudagi tugmalar",'callback_data'=>"asosiy"]],
[['text'=>"⚠️ O'z holiga qaytarish",'callback_data'=>"reset"]],
]]));
exit();
}

if($data == "tugmalar"){
del();
sms($cid2,"<b>Quyidagilardan birini tanlang:</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"🖥 Asosiy menyudagi tugmalar",'callback_data'=>"asosiy"]],
[['text'=>"⚠️ O'z holiga qaytarish",'callback_data'=>"reset"]],
]]));
exit();
}


if($data == "reset"){
edit($cid2,$mid2,"<b>Barcha tahrirlangan tugmalar bilan bog'liq sozlamalar o'chirib yuboriladi va birlamchi sozlamalar o'rnatiladi.</b>

<i>Ushbu jarayonni davom ettirsangiz, avvalgi sozlamalarni tiklay olmaysiz, rozimisiz?</i>",json_encode([
'inline_keyboard'=>[
[['text'=>"✅ Roziman",'callback_data'=>'roziman']],
[['text'=>"◀️ Orqaga",'callback_data'=>"tugmalar"]],
]]));
}

if($data == "roziman"){
edit($cid2,$mid2,"<b>Tugma sozlamalari o'chirilib, birlamchi sozlamalar o'rnatildi.</b>",json_encode([
'inline_keyboard'=>[
[['text'=>"Orqaga",'callback_data'=>"tugmalar"]],
]]));
deleteFolder("tugma");
}

if($data == "asosiy"){	
edit($cid2,$mid2,"<b>Quyidagilardan birini tanlang:</b>",json_encode([
'inline_keyboard'=>[
[['text'=>$key1,'callback_data'=>"tugma=key1"]],
[['text'=>$key2,'callback_data'=>"tugma=key2"],['text'=>$key3,'callback_data'=>"tugma=key3"]],
[['text'=>$key4,'callback_data'=>"tugma=key4"],['text'=>$key5,'callback_data'=>"tugma=key5"]],
[['text'=>$key6,'callback_data'=>"tugma=key6"]],
[['text'=>"Orqaga",'callback_data'=>"tugmalar"]]
]]));
}

if(mb_stripos($data,"tugma=")!==false){
del();
sms($cid2,"<b>Tugma uchun yangi nom yuboring:</b>",$boshqarish);
put("step/$cid2.step",$data);
exit();
}

if(mb_stripos($step,"tugma=")!==false and in_array($cid,$admin)){
$tip=explode("=",$step)[1];
if(isset($text)){
put("tugma/$tip.txt",$text);
sms($cid,"<b>Qabul qilindi!</b>

<i>Tugma nomi</i> <b>$text</b> <i>ga o'zgartirildi.</i>",$panel);
unlink("step/$cid.step");
exit();
}
}

if(is_numeric($text) and joinchat($cid)==true){
$rew = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM animelar WHERE id = $text"));
if($rew){
$cs = $rew['qidiruv'] + 1;
mysqli_query($connect,"UPDATE animelar SET qidiruv = $cs WHERE id = $text");
bot('sendPhoto',[
'chat_id'=>$cid,
'photo'=>$rew['rams'],
'caption'=>"<b>🎬 Nomi: $rew[nom]</b>

🎥 Qismi: $rew[qismi]
🌍 Davlati: $rew[davlat]
🇺🇿 Tili: $rew[tili]
📆 Yili: $rew[yili]
🎞 Janri: $rew[janri]

🔍Qidirishlar soni: $cs

🍿 $anime_kanal",
'parse_mode'=>"html",
'reply_markup'=>json_encode([
'inline_keyboard'=>[
[['text'=>"YUKLAB OLISH 📥",'callback_data'=>"yuklanolish=$text=1"]]
]
])
]);
exit();
}else{
sms($cid,"<b>[ $text ] kodiga tegishli anime topilmadi😔</b>

• Boshqa Kod yuboring",null);
exit();
}
}

if(isset($message) and empty($step)){
if(joinchat($cid)==true){
$text = mysqli_real_escape_string($connect,$text);
$rew = mysqli_query($connect,"SELECT * FROM animelar WHERE nom LIKE '%$text%' LIMIT 0,10");
$c = mysqli_num_rows($rew);
$i = 1;
while($a = mysqli_fetch_assoc($rew)){
$k[]=['text'=>"$i. $a[nom]",'callback_data'=>"loadAnime=".$a['id']];
$i++;
}
$keyboard2=array_chunk($k,1);
$kb=json_encode([
'inline_keyboard'=>$keyboard2,
]);
if(!$c){
sms($cid,"🙁 Natija mavjud emas!",null);
}else{
bot('sendMessage',[
'chat_id'=>$cid,
'reply_to_message_id'=>$mid,
'text'=>"<b>⬇️ Qidiruv natijalari:</b>",
'parse_mode'=>"html",
'reply_markup'=>$kb
]);
}
}
}

//<---- @obito_us ---->//