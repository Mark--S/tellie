function(doc) {
    var index = "";
    if( doc.index )
        index = doc.index;
    if( typeof doc.run === 'undefined' && !doc.run_range && typeof doc.timestamp === 'undefined' ) {
        emit([doc.type, index, doc.version, doc.pass], null);
    }
}
