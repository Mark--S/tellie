function(doc) {
    var index = "";
    if( doc.index )
        index = doc.index;
    if( typeof doc.run !== 'undefined' ) {
        emit([doc.type, index, doc.run, doc.version, doc.pass], null);
    }
    else if( doc.run_range ) {
        for(var run=doc.run_range[0]; run <= doc.run_range[1]; i++) {
            emit([doc.type, index, run, doc.version, doc.pass], null);
        }
    }
}
