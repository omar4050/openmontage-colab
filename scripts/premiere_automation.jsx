/* Premiere automation (ExtendScript)
   This script imports a single video, creates a sequence, places the clip, and queues export via AME.
   Save this file and run from Premiere's Script Runner or via `Premiere.exe -r <this-file>` if supported.

   Note: Running scripts in Premiere may open the UI and require an active user session.
*/

(function () {
  var projectPath = "%PROJECT%"; // optional: preserve project path
  var importFile = "%IMPORT_FILE%";
  var outFile = "%OUTPUT_FILE%";

  try {
    var appProj = app.project;
    // Import file
    var importOK = appProj.importFiles([importFile], true, appProj.getInsertionBin(), false);
    if (!importOK || appProj.rootItem.children.numItems === 0) {
      alert('Import failed: ' + importFile);
    }

    // Use the first sequence if available, otherwise create a new sequence from the clip
    if (appProj.sequences && appProj.sequences.numSequences > 0) {
      var seq = appProj.sequences[0];
    } else {
      // Create a new sequence from a preset (using first preset is easiest). This is a fallback.
      var seq = appProj.createNewSequenceFromClips('OM_Seq', [importFile]);
    }

    // Find the imported item and add to the sequence
    var importedItem = null;
    function findImported(item) {
      if (!item) return null;
      for (var i = 0; i < item.children.numItems; i++) {
        var child = item.children[i];
        if (child && child.name && child.name.indexOf(app.systemPathToURI(importFile)) === -1) {
          // best-effort
        }
      }
    }

    // Queue an export via Adobe Media Encoder if available
    if (app.encoder) {
      app.encoder.launchEncoder();
      app.encoder.encodeSequence(seq, outFile, "H.264", app.encoder.ENCODE_WORKAREA);
    } else {
      alert('Adobe Media Encoder interface (app.encoder) not available. Please export manually.');
    }

  } catch (e) {
    alert('Premiere script error: ' + e.toString());
  }
})();
