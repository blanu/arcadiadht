function getDocs()
{
  log('get docs');
  var url='/db/'+dbid;
  $.getJSON(url, gotDocs);
}

function gotDocs(docs)
{
  log('got docs');
  log(docs);
  $('#docs').empty();
  for(var x=0; x<docs.length; x++)
  {
    $('#docs').append('<li><a class="doclink" href="/dashboard/'+dbid+'/'+docs[x]+'">'+docs[x]+'</a></li>');
  }
}

function addDoc(docname)
{
  log('dbname: '+docname);
  var url="/db/"+dbid+'/'+docname;
  $.post(url, JSON.stringify(null));
}

function addDbDialog()
{
  $("#addDbDialog").dialog({
    buttons: {
      "Add": function() {
        var dbname=$("#addDbNameField").val();
        addDoc(dbname);
        $(this).dialog("close");
      },
      "Cancel": function() {
        $(this).dialog("close");
      }
    }
  });

  return false;
}

function initDatabase()
{
  log('listening docs-'+userid+'-'+dbid);
  Web2Peer.listen('docs-'+userid+'-'+dbid, gotDocs);

  $("#addDbButton").click(addDbDialog);

  getDocs();
}

$(document).ready(initDatabase);