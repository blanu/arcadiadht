function gotData(value)
{
  $('#value').val(JSON.stringify(value));
}

function get()
{
  var key=$('#key').val();

  log('get: '+key);
  var url="/client/data/"+key;
  $.getJSON(url, gotData);
}

function put()
{
  var key=$('#key').val();
  var value=JSON.parse($('#value').val());
  log('value: '+value);

  log('put: '+key);
  var url="/client/data/"+key;
  $.post(url, {'value': JSON.stringify(value)});
}

function initIndex()
{
  $("#getButton").click(get);
  $("#putButton").click(put);
}

$(document).ready(initIndex);
