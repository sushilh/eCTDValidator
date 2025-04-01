require.config({
  baseUrl: 'https://static.oracle.com/cdn/jet/v14.1.0',
  paths: {
    'knockout': '3rdparty/knockout/knockout-3.5.1',
    'jquery': '3rdparty/jquery/jquery-3.6.0.min',
    'ojs': 'default/js',
    'ojL10n': '3rdparty/ojL10n/ojL10n',
    'ojtranslations': 'default/js/resources',
    'text': '3rdparty/require/text',
    'signals': '3rdparty/js-signals/signals',
    'ojdnd': '3rdparty/dnd-polyfill/dnd-polyfill-1.0.0',
    'css': '3rdparty/require-css/css.min'
  }
});

require(['ojs/ojbootstrap', 'knockout', 'jquery', 'ojs/ojfilepicker', 'ojs/ojbutton', 'ojs/ojprogress-bar'],
  function (Bootstrap, ko) {
    function ViewModel() {
      const self = this;
      self.fileName = ko.observable('');
      self.uploading = ko.observable(false);
      self.result = ko.observable('');

      self.selectListener = (event) => {
        const files = event.detail.files;
        if (files.length > 0) {
          self.fileName(files[0].name);
          const formData = new FormData();
          formData.append('file', files[0]);

          self.uploading(true);
          fetch('http://localhost:5000/validate', {
            method: 'POST',
            body: formData
          })
          .then(response => response.json())
          .then(data => {
            self.result(JSON.stringify(data, null, 2));
            self.uploading(false);
          })
          .catch(err => {
            self.result('Validation failed: ' + err);
            self.uploading(false);
          });
        }
      };
    }

    Bootstrap.whenDocumentReady().then(function () {
      ko.applyBindings(new ViewModel(), document.getElementById('container'));
    });
  }
);
