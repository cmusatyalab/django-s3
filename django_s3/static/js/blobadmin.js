django.jQuery(function() {
  var $ = django.jQuery;
  var uploading = 0;
  var csrf_token = $('input[type="hidden"][name="csrfmiddlewaretoken"]').
      attr('value');

  window.onbeforeunload = function(ev) {
    if (uploading) {
      return 'Navigating away from this page will cancel ' + uploading +
          ' upload' + (uploading == 1 ? '' : 's') + '.';
    }
  }

  $('.upload-field').each(function(i, d) {
    var blob_id = $(d).attr('data-blob');
    var start_url = $(d).attr('data-upload-start');
    var chunk_url = $(d).attr('data-upload-chunk');
    var finish_url = $(d).attr('data-upload-finish');
    var r = new Resumable({
      target: chunk_url,
      chunkSize: 10 << 20,
      query: {
        blob: blob_id,
        csrfmiddlewaretoken: csrf_token,
      },
      testChunks: false,
      maxFiles: 1,
    });

    function fail(msg) {
      r.cancel();
      var div = $('<div class="upload-notice"></div>').text(msg);
      $(d).html(div);
    }

    if (!r.support) {
      fail("Upload not supported");
      return;
    }

    var browse = $('<button type="button" class="button upload">Upload</button>');
    browse.appendTo(d);
    r.assignBrowse(browse[0]);
    // assignBrowse() places a file input inside the browse button and
    // configures it to overlap the actual button, which does not work
    // on Firefox.  Move the input outside the button, hide it, and
    // trigger it programmatically.
    browse.children('input').hide().insertAfter(browse);
    browse.click(function(ev) {
      ev.preventDefault();
      $(this).next('input').click();
    });

    var progressbar = $('<div class="progressbar"></div>').hide().appendTo(d);
    var progress = $('<div class="progress"></div>').appendTo(progressbar);

    r.on('fileAdded', function() {
      uploading++;
      browse.hide();
      progressbar.show();
      $.ajax({
        type: 'POST',
        url: start_url,
        data: {
          blob: blob_id,
          csrfmiddlewaretoken: csrf_token,
        },
        dataType: 'json',
        success: function(data) {
          r.opts.query.token = data.token;
          r.upload();
        },
        error: function() {
          fail("Couldn't start upload");
          uploading--;
        },
      });
    });
    r.on('progress', function() {
      progress.width(r.progress() * 100 + '%');
    });
    r.on('complete', function() {
      $.ajax({
        type: 'POST',
        url: finish_url,
        data: {
          blob: blob_id,
          token: r.opts.query.token,
          csrfmiddlewaretoken: csrf_token,
        },
        dataType: 'json',
        success: function(data) {
          progressbar.hide();
          $(d).text(data.size);
          uploading--;
        },
        error: function() {
          fail("Couldn't complete upload");
          uploading--;
        },
      });
    });
    r.on('error', function() {
      fail("Couldn't upload file");
      uploading--;
    });
  });
});
