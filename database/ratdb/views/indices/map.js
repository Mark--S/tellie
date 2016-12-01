function(doc) {
    if(doc.index!==null)
        emit([doc.type,doc.index.toString()],null);
}
