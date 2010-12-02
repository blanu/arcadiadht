function received(data)
{
  log('message:');
  log(data);
  $("#messages").append("<li>"+data+"</li>");
}

function sendMessage()
{
  Web2Peer.send('test', 'test message: '+new Date());
}

function websocketInit()
{
  log('wsinit');
  Web2Peer.init("yourapikey");
  Web2Peer.listen('test', received);

  $("#send").click(sendMessage);
}

$(document).ready(websocketInit);
