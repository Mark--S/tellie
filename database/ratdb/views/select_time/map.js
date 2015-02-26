function(doc) {
    var index = "";
    if( doc.index )
        index = doc.index;
    if( typeof doc.timestamp !== 'undefined' ) {
        emit([doc.type, index, doc.timestamp, doc.version, doc.pass], null);
    }
}
