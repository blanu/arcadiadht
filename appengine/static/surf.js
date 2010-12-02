function _ajax_request(url, data, callback, type, method) {
    if (jQuery.isFunction(data)) {
        callback = data;
        data = {};
    }
    return jQuery.ajax({
        type: method,
        url: url,
        data: data,
        success: callback,
        dataType: type
        });
}

jQuery.extend({
    put: function(url, data, callback, type) {
        return _ajax_request(url, data, callback, type, 'PUT');
    },
    delete_: function(url, data, callback, type) {
        return _ajax_request(url, data, callback, type, 'DELETE');
    }
});

wave={};
wave.gadgets=[];
wave.waveid=null;
wave.stateCallback=null;
wave.participantCallback=null;
wave.attachmentsCallback=null;
wave.participants=[];
wave.attachments=[];
wave.updating=false;

waves={};

$(function() {
  getWave = function()
  {
    return wave;
  };
});

function getWave()
{
  return wave;
}

window.getWave=function()
{
  return wave;
}

this.getWave=function()
{
  return wave;
}

function parentPrint()
{
  alert("hatcha!");
}

wave.noop=function()
{
}

wave.Participant=function(id, displayName, thumbnailUrl)
{
  this.id=id;
  this.displayName=displayName;
  this.thumbnailUrl=thumbnailUrl;

  this.test = function()
  {
    log('test complete!');
  }

  this.getId = function()
  {
    return this.id;
  }

  this.getDisplayName = function()
  {
    return this.displayName;
  }

  this.getThumbnailUrl = function()
  {
    return this.thumbnailUrl;
  }
}

wave.Scratch=function(newState)
{
  this.state=newState;

  this.submitDelta=function(delta)
  {
    log("scratch delta:");
    log(delta);
    for(var key in delta)
    {
      var value=delta[key];

      log('setting');
      log(key);
      log(value);

      this.state[key]=value;
    }

    log('saving:');
    log(this.state);

    saveScratch(this.state);
  }

  this.get=function(key, opt_default)
  {
    var value=this.state[key];
    if(value)
    {
      return value;
    }
    else
    {
      return opt_default;
    }
  }

  this.getKeys=function()
  {
    var keys=[];
    for(var key in this.state)
    {
      keys.push(key);
    }
    return keys;
  }

  this.reset=function()
  {
    saveScratch({});
  }

  this.submitValue=function(key, value)
  {
    var delta={};
    delta[key]=value
    this.submitDelta(delta);
  }

  this.toString=function()
  {
    return JSON.stringify(this.state);
  }
}

wave.Shard=function(newState)
{
//  log('class this: '+this);
  this.state=newState;

  this.printThis=function()
  {
//    log('print this: '+this);
  }

  this.submitDelta=function(delta)
  {
//    log('method this: '+this);
//    log('state: '+newState);
    for(var key in delta)
    {
      var value=delta[key];

//      log('for this: '+this);
      this.state[key]=value;
    }

    saveState(this.state);
  }

  this.get=function(key, opt_default)
  {
    var value=this.state[key];
    if(value)
    {
      return value;
    }
    else
    {
      return opt_default;
    }
  }

  this.getKeys=function()
  {
    var keys=[];
    for(var key in this.state)
    {
      keys.push(key);
    }
    return keys;
  }

  this.reset=function()
  {
    saveState({});
  }

  this.submitValue=function(key, value)
  {
    var delta={};
    delta[key]=value
    this.submitDelta(delta);
  }

  this.toString=function()
  {
    return JSON.stringify(this.state);
  }
}

wave.State=function()
{
  this.state={};

  this.get=function(key, opt_default)
  {
    var value=this.state[key];
    if(value)
    {
      return value;
    }
    else
    {
      return opt_default;
    }
  }

  this.getKeys=function()
  {
    var keys=[];
    for(var key in this.state)
    {
      keys.push(key);
    }
    return keys;
  }

  this.reset=function()
  {
    shard=this.getShard();
    shard.reset();
  }

  this.getScratch=function()
  {
    var scratchState=this.state['scratch'];
    if(!scratchState)
    {
      scratchState={};
    }

    return new wave.Scratch(scratchState);
  }

  this.getShard=function()
  {
//    log('state: '+JSON.stringify(this.state));
//    log('userid: '+wave.userid);
    var shardState=this.state[wave.userid];
//    log('shardState: '+shardState);
    if(!shardState)
    {
      shardState={};
    }

    return new wave.Shard(shardState);
  }

  this.getShards=function()
  {
    var shards=[];
    for(var key in this.state)
    {
      shards.push(new wave.Shard(this.state[key]));
    }

    return shards;
  }

  this.submitDelta=function(delta)
  {
    shard=this.getShard();
    shard.submitDelta(delta);
  }

  this.submitValue=function(key, value)
  {
    var delta={};
    delta[key]=value
    this.submitDelta(delta);
  }

  this.update=function(state)
  {
    this.state=state;
  }

  this.toString=function()
  {
    return JSON.stringify(this.state);
  }
}

wave.state=new wave.State();

wave.getParticipantById=function(id)
{
  return pmap[id];
}

wave.setStateCallback=function(callback, opt_context)
{
  log('setStateCallback');
  wave.stateCallback=callback;

  startUpdatingWave();
}

wave.setParticipantCallback=function(callback, opt_context)
{
  log('setParticipantCallback');
  wave.participantCallback=callback;

  startUpdatingWave();
}

wave.setAttachmentsCallback=function(callback, opt_context)
{
  log('setAttachmentsCallback');
  wave.attachmentsCallback=callback;

  startUpdatingWave();
}

wave.getState=function()
{
  return wave.state;
}

wave.getParticipants=function()
{
  return wave.participants;
}

wave.getViewer=function()
{
  return wave.viewer;
}

wave.getWaveId=function()
{
  return wave.waveid;
}

wave.isInWaveContainer=function()
{
  return typeof(wave)!=undefined && wave!=null;
}

wave.isPlayback=function()
{
  return false;
}

wave.getMode=function()
{
  return 0;
}

wave.log=log;

wave.setModeCallback=wave.noop;

wave.setSnippet=wave.noop;

function saveState(state)
{
  var url='/wave/shard/'+wave.waveid;

  log('saving state: '+JSON.stringify(state));

  $.put(url, JSON.stringify(state));
}

function saveScratch(state)
{
  var url='/wave/scratch/'+wave.waveid;

  log('saving scratch: '+JSON.stringify(state));

  $.put(url, JSON.stringify(state));
//  $.put(url, state);
}

function getWaveId()
{
  log("getWaveId");
  var loc=window.location+'';
  log("loc: "+loc+" "+typeof(loc));
  var parts=loc.split('/');
  log("parts: "+parts);
  log("length: "+parts.length);
  wave.waveid=parts[parts.length-1];
  log("waveid: "+wave.waveid);
}

function joinWave()
{
  var url='/wave/join/'+wave.waveid
  $.post(url);
}

function startUpdatingWave()
{
  if(!wave.updating)
  {
    updateWave();

    wave.updating=true;
    periodicUpdateWave();
  }
}

function periodicUpdateWave()
{
  Web2Peer.listen('wave-'+wave.waveid+'-state', waveStateResults);
  Web2Peer.listen('wave-'+wave.waveid+'-participants', waveParticipantsResults);
  Web2Peer.listen('wave-'+wave.waveid+'-attachments', waveAttachmentsResults);
}

function updateWave()
{
  getWaveParticipants();
  getWaveState();
  getWaveAttachments();
}

function getWaveParticipants()
{
  log('gwp');
  var url='/wave/participants/'+wave.waveid
  $.getJSON(url, waveParticipantsResults);
}

function waveParticipantsResults(data)
{
  log('wpr: '+data+" "+typeof(data));
  wave.participants=[];
  wave.pmap={};

  if(data)
  {
    if(typeof(data)=='string')
    {
      data=JSON.parse(data);
    }

    for(var key in data)
    {
      log('key: '+key);
      var value=data[key];
      var p=new wave.Participant(key, value.nickname, null);
      log("p:");
      log(p);
      log('dn: '+p.getDisplayName());
      wave.participants.push(p);
      wave.pmap[key]=p;
    }
  }

  if(!wave.viewer)
  {
    wave.viewer=wave.pmap[wave.userid];
  }

  if(wave.participantsCallback)
  {
    log('calling participants callback');
    wave.participantsCallback();
  }
}

function getWaveAttachments()
{
  log('gwa');
  var url='/wave/attachments/'+wave.waveid
  $.getJSON(url, waveAttachmentsResults);
}

function waveAttachmentsResults(data)
{
  log('war: '+data+" "+typeof(data));

  if(data)
  {
    if(typeof(data)=='string')
    {
      data=JSON.parse(data);
    }

    wave.attachments=data;
  }
  else
  {
    wave.attachments=[];
  }

  if(wave.attachmentsCallback)
  {
    wave.attachmentsCallback(wave.attachments);
  }
}

function getWaveState()
{
  log('gws');
  var url='/wave/state/'+wave.waveid
  $.getJSON(url, waveStateResults);
}

function waveStateResults(data)
{
  log('wsr:');
  log(typeof(data));
  log(data);
  if(data)
  {
    if(typeof(data)=='string')
    {
      data=JSON.parse(data);
    }
    wave.state.update(data);
  }
  else
  {
    wave.state.update({});
  }

  if(wave.stateCallback)
  {
    log('calling state callback');
    wave.stateCallback();
  }
}

function loadGadgets()
{
  log('loading gadgets...');
  for(var x=0; x<wave.gadgets.length; x++)
  {
    log('loading '+wave.waveid+" "+x);
    log($('#'+wave.waveid).size());
    log($('#'+wave.waveid+' .gadgets').size());
    $("#"+wave.waveid+" .gadgets").append('<div id="'+wave.gadgets[x].id+'" class="gadgetContainer"><iframe name="'+wave.gadgets[x].id+'" src="'+wave.gadgets[x].url+'" height="550px" width="100%"/></div>');
    waves[wave.gadgets[x].id]=new Wave();
  }
}

function refreshGadgetIds()
{
  $('iframe').each(function() {
    var name=$(this).attr('name');
    var frame=window.frames[name];
    log('frame: '+name);
    log(frame);
    frame.setGadgetId(name);
  });
}

function initSurf()
{
  // Tabs
  $('#tabs').tabs();

  var p=new wave.Participant();
  p.test();

  getWaveId();
  joinWave();

  Web2Peer.init("wave");

  loadGadgets();
}

$(document).ready(initSurf);
