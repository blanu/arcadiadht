var selectPath=null;

function typeOf(value) {
    var s = typeof value;
    if (s === 'object') {
        if (value) {
            if (value instanceof Array) {
                s = 'array';
            }
        } else {
            s = 'null';
        }
    }
    return s;
}

function encode(path)
{
  var s='';
  for(var x=0; x<path.length; x++)
  {
    s=s+JSON.stringify(path[x]);
    if(x<path.length-1)
    {
      s=s+'/';
    }
  }

  return s;
}

function decode(path)
{
  var a=[];
  var parts=path.split('/');
  for(var x=0; x<parts.length; x++)
  {
    a.append(JSON.parse(parts[x]));
  }

  return a;
}

function lookup(doc, docPath)
{
  log('docPath:');
  log(docPath);
  while(docPath.length>0)
  {
    var key=docPath.shift();
    doc=doc[key];
  }

  return doc;
}

function renderSimpleCell(doc, docPath, cls, container)
{
  var edp=encode(docPath);

  container.empty();
  container.append('<div class="'+cls+'" docPath="'+edp+'">'+JSON.stringify(doc)+'</div>');
}

function renderCell(docPath, containerPath)
{
  log('renderCell '+docPath+' '+containerPath);

  var container=$(containerPath);
  container.empty();

  var doc=lookup(fullDoc, docPath);

  var typ=typeOf(doc)
  switch(typ)
  {
    case 'null':
    case 'string':
    case 'number':
    case 'boolean':
      renderSimpleCell(doc, docPath, typ, container);
      break;
    case 'array':
      log('rendering array');
      container.append('<table class="array"><tbody><tr></tr></tbody></table>');
      var sub=container.children('table').children('tbody').children('tr').first();
      for(var x=0; x<doc.length; x++)
      {
        sub.append('<td></td>');
        var td=sub.children('td').first();
        renderCell(doc[x], td);
      }
      break;
    case 'object':
      container.append('<div class="map"/>');
      var sub=container.children('div').first();
      for(var key in doc)
      {
        sub.append('<div class="map-pair"><div class="map-key"></div><div class="map-value"></div></div>');
        var pair=sub.children('div').first();
        var keyCell=pair.children('div').first();
        var valueCell=pair.children('div').last();
        renderCell(key, keyCell);
        renderCell(value, valueCell);
      }
      break;
    default:
      log('Unknown type '+typeof(doc)+' '+doc);
  }
}

function cellType(docPath)
{
  var cell=lookup(fullDoc, docPath);
  return typeOf(cell);
}

function selectCell(docPath)
{
  var typ=cellType(docPath);

  $('input#type').attr('checked', false);
  $('input[name="type"][value="'+typ+'"]').attr('checked', 'true');

  $([path="'+docPath+'"]).addClass('selected');

  selectPath=docPath;
}

function renderEditor()
{
  log('renderEditor');

  renderCell([], '#editorMain');
  selectCell([]);
}

/* ---------------------- Conversions --------------------------- */

function identity(val)
{
  return val;
}

function nullval(val)
{
  return null;
}

function none(val)
{
  return 1;
}

function nzero(val)
{
  return 0;
}

function sempty(val)
{
  return '';
}

function sjson(val)
{
  return JSON.stringify(val);
}

function delist(val, type, def)
{
  if(val.length==1)
  {
    if(typeof(val[0])==type)
    {
      return val[0];
    }
    else
    {
      return def;
    }
  }
  else
  {
    return def;
  }
}

function sdelist(val)
{
  return delist(val, 'string', '""');
}

function nparse(val)
{
  try
  {
    val=parseFloat(val);
    log('nparse: '+val);
    if(isNaN(val))
    {
      return 0;
    }
    else
    {
      return val;
    }
  }
  catch(error)
  {
    return 0;
  }
}

function ndelist(val)
{
  return delist(val, 'number', 0);
}

function btrue(val)
{
  return true;
}

function bfalse(val)
{
  return false;
}

function bdelist(val)
{
  return delist(val, 'boolean', false);
}

function aempty(val)
{
  return [];
}

function aenlist(val)
{
  return [val];
}

function mempty(val)
{
  return {};
}

var converters={
  'null': {
    'null': identity,
    'string': nullval,
    'number': nullval,
    'boolean': nullval,
    'array': nullval,
    'map': nullval
  },
  'string': {
    'null': sempty,
    'string': identity,
    'number': sjson,
    'boolean': sjson,
    'array': sdelist,
    'map': sempty
  },
  'number': {
    'null': nzero,
    'string': nparse,
    'number': identity,
    'boolean': function(val) {
      if(val)
      {
        return 1;
      }
      else
      {
        return 0;
      }
    },
    'array': ndelist,
    'map': nzero
  },
  'boolean': {
    'null': bfalse,
    'string': function(val) {
      try
      {
        return parseBoolean(val);
      }
      catch(error)
      {
        return false;
      }
    },
    'number': function(val) {
      if(val>0)
      {
        return true;
      }
      else
      {
        return false;
      }
    },
    'boolean': identity,
    'array': bdelist,
    'map': bfalse
  },
  'array': {
    'null': aempty,
    'string': aenlist,
    'number': aenlist,
    'boolean': aenlist,
    'array': identity,
    'map': aenlist
  },
  'map': {
    'null': mempty,
    'string': mempty,
    'number': mempty,
    'boolean': mempty,
    'array': mempty,
    'map': identity
  }
};

function convert(fromType, toType, value)
{
  log('convert '+fromType+' '+toType+' '+value);
  var f=converters[toType][fromType];
  log('f: '+f);
  return f(value);
}

function controlType()
{
  return $('input[name="type"]')
         .filter(function(index) {return $(this).attr('checked');})
         .attr('value');
}

function changeType()
{
  log('selectPath:');
  log(selectPath);
  var val=lookup(fullDoc, selectPath);
  var fromType=typeOf(val);
  log('fromType: '+fromType);
  var toType=controlType();
  log('toType: '+toType);

  var newval=convert(fromType, toType, val);
  log('newval: '+newval+' '+typeof(newval));

  var container=$('[docPath="'+selectPath+'"]').parent();
  log('container:');
  log(container);
  container.empty();
  log(container);
  renderCell(selectPath, container);
  selectCell(selectPath);
}
