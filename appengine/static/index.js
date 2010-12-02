function getDbs()
{
  log('get dbs');
  var url='/db';
  $.getJSON(url, gotDbs);
}

function gotDbs(dbs)
{
  log('got dbs');
  log(dbs);
  $('#dbs').empty();
  for(var x=0; x<dbs.length; x++)
  {
    $('#dbs').append('<li><a class="dblink" href="/dashboard/'+dbs[x]+'">'+dbs[x]+'</a></li>');
  }
}

function addDb(dbname)
{
  log('dbname: '+dbname);
  var url="/db/new";
  $.post(url, JSON.stringify({'dbid': dbname}));
}

function addDbDialog()
{
  $("#addDbDialog").dialog({
    buttons: {
      "Add": function() {
        var dbname=$("#addDbNameField").val();
        addDb(dbname);
        $(this).dialog("close");
      },
      "Cancel": function() {
        $(this).dialog("close");
      }
    }
  });

  return false;
}

function initIndex()
{
  log('listening on dbs-'+userid);
  Web2Peer.listen('dbs-'+userid, gotDbs);

  $("#addDbButton").click(addDbDialog);

  getDbs();
}

$(document).ready(initIndex);