function (note) {
  var removeDigitsRegEx = /\s\d{4}$/;
  var removeTrailingPeriod = /[\.]$/;
  var et = require('elementtree');
  var XML = et.XML;
  
  var entryTypes = {
    'article': {
      'description': 'An article from a journal or magazine.',
      'required': ['author', 'title', 'journal', 'year'],
      'optional': ['key', 'volume', 'number', 'pages', 'month', 'note']
    },
    'book': {
      'description': 'A book with an explicit publisher',
      'required': ['author|editor', 'title', 'publisher'],
      'optional': ['key', 'volume|number', 'series', 'address', 'edition', 'month', 'year', 'note']
    },
    'booklet': {
      'description': 'A work that is printed and bound, but without a named publisher or sponsoring institution.',
      'required': ['title'],
      'optional': ['key', 'author', 'howpublished', 'address', 'month', 'year', 'note']
    },
    'conference': {
      'description': 'The same as @inproceedings',
      'required': ['author', 'title', 'booktitle', 'year'],
      'optional': ['key', 'editor', 'volume|number', 'series', 'pages', 'address', 'month', 'organization', 'publisher', 'note']
    },
    'inbook': {
      'description': 'A part of a book, which may be a chapter (or section or whatever) and/or a range of pages.',
      'required': ['author|editor', 'title', 'chapter|pages', 'publisher', 'year'],
      'optional': ['key', 'volume|number', 'series', 'type', 'address', 'edition', 'month', 'note']
    },
    'incollection': {
      'description': 'A part of a book having its own title.',
      'required': ['author', 'title', 'booktitle', 'publisher', 'year'],
      'optional': ['key', 'editor', 'volume|number', 'series', 'type', 'chapter', 'pages', 'address', 'edition', 'month', 'note']
    },
    'inproceedings': {
      'description': 'An article in a conference proceedings.',
      'required': ['author', 'title', 'booktitle', 'year'],
      'optional': ['key', 'editor', 'volume|number', 'series', 'pages', 'address', 'month', 'organization', 'publisher', 'note']
    },
    'manual': {
      'description': 'Technical documentation.',
      'required': ['title'],
      'optional': ['key', 'author', 'organization', 'address', 'edition', 'month', 'year', 'note']
    },
    'mastersthesis': {
      'description': 'A Master\'s thesis',
      'required': [ 'author', 'title', 'school', 'year'],
      'optional': ['key', 'type', 'address', 'month', 'note']
    },
    'misc': {
      'description': 'Use this type when nothing else fits.',
      'required': [],
      'optional': ['key', 'author', 'title', 'howpublished', 'month', 'year', 'note']
    },
    'phdthesis': {
      'description': 'A PhD thesis.',
      'required': [ 'author', 'title', 'school', 'year'],
      'optional': ['key', 'type', 'address', 'month', 'note']
    },
    'proceedings': {
      'description': 'The proceedings of a conference.',
      'required': ['title', 'year'],
      'optional': ['key', 'editor', 'volume|number', 'series', 'address', 'month', 'organization', 'publisher', 'note']
    },
    'techreport': {
      'description': 'A report published by a school or other institution, usually numbered within a series.',
      'required': ['author', 'title', 'institution', 'year'],
      'optional': ['key', 'type', 'number', 'address', 'month', 'note']
    },
    'unpublished': {
      'description': 'A document having an author and title, but not formally published.',
      'required': ['author', 'title', 'note'],
      'optional': ['key', 'month', 'year']
    }
  };
  
  var firstOrNull = function(array){
    if (array.length > 0){
      return array[0].text;
    } else {
      return null;
    }
  };
  
  var firstOrNullTitle = function(array){
    if (array.length > 0){
      let title = '';
      array[0].itertext( function(text){
        title = title + text;
      });
      return title;
    } else {
      return null;
    }
  };
  
  var getEntryElement = function(xmlString) {
    var tree = new et.ElementTree(XML(xmlString));
    var root = tree.getroot();
    var entryElement;
    
    if (root.tag === 'dblp') {
      var children = root._children
      if (children.length === 1) {
        entryElement = children[0];
       } else {
        console.log('something went wrong');
      }
    } else {
      entryElement = tree.getroot();
    }
    return entryElement;
  };
  
  var entryToData = function(entryElement) {
    var data = {};
    data.type = entryElement.tag;
    data.key = entryElement.attrib.key;
    data.publtype = entryElement.attrib.publtype
    data.authors = [];
    data.authorids = [];
    entryElement.iter('author', function(element){
      data.authors.push(element.text.replace(removeDigitsRegEx, '').replace('(','').replace(')',''));
      data.authorids.push('https://dblp.org/search/pid/api?q=author:' + element.text.split(' ').join('_') + ':')
    })
    
    data.title = firstOrNullTitle(entryElement.findall('title')).replace('\n', '').replace(removeTrailingPeriod, '');
    data.year = parseInt(firstOrNull(entryElement.findall('year')));
    data.month = firstOrNull(entryElement.findall('month'));
    
    if (data.year) {
      var cdateString = data.month ? data.month + ' ' + data.year : data.year;
      data.cdate = Date.parse(cdateString);
    }
    
    data.journal = firstOrNull(entryElement.findall('journal'));
    data.volume = firstOrNull(entryElement.findall('volume'));
    data.number = firstOrNull(entryElement.findall('number'));
    data.chapter = firstOrNull(entryElement.findall('chapter'));
    data.pages = firstOrNull(entryElement.findall('pages'));
    data.url = firstOrNull(entryElement.findall('ee'));
    data.isbn = firstOrNull(entryElement.findall('isbn'));
    data.booktitle = firstOrNull(entryElement.findall('booktitle'));
    data.crossref = firstOrNull(entryElement.findall('crossref'));
    data.publisher = firstOrNull(entryElement.findall('publisher'));
    data.school = firstOrNull(entryElement.findall('school'));
    Object.keys(data).forEach((key) => (data[key] == null) && delete data[key]);
      return data
    };
    
  var dataToBibtex = function(data) {
    var bibtexIndent = '  ';
    var bibtexComponents = [
      '@',
      data.type,
      '{',
      'DBLP:',
      data.key,
      ',\n'];
      
    var omittedFields = ['type', 'key', 'authorids'];
    var typeDetails = entryTypes[data.type] ? entryTypes[data.type] : entry_types.misc;
    
    var requiredFields = typeDetails.required
    var optionalFields = typeDetails.optional
    
    var dataEntries = Object.entries(data);
    
    for ([field, value] of dataEntries){
      if (value && !omittedFields.includes(field)) {
        var valueString;
        if (Array.isArray(value)) {
          valueString = value.join(' and ');
          if (field.endsWith('s')) {
            field = field.substring(0, field.length-1);
          }
        } else {
          valueString = String(value);
        }
        
        for (const component of [bibtexIndent, field, "={", valueString, "},\n"]) {
          bibtexComponents.push(component);
        }
      }
    }
    
    bibtexComponents[bibtexComponents.length-1] = bibtexComponents[bibtexComponents.length-1].replace(',\\n', '\\n');
    bibtexComponents.push("}\n");
    return bibtexComponents.join('');
  };
    
  var entryElement = getEntryElement(note.content.dblp);
  
  if (entryElement != null) {
    var data = entryToData(entryElement);
    var newContent = {};
    newContent.venue = data.journal || data.booktitle;
    if (data.key) {
      var keyParts = data.key.split('/');
      var venueidParts = ['dblp.org'];
      // get all but the last part of the key\n      
      for (var i=0; i<keyParts.length-1; i++) {
        var keyPart = keyParts[i];
        if (i === keyParts.length-2) {
          keyPart = keyPart.toUpperCase();
        }
        venueidParts.push(keyPart);
      }
      
      // we might not want this later
      if (data.year) {
        venueidParts.push(data.year);
        // new addition at Andrew's request
        newContent.venue += ' ' + String(data.year)
      }
      newContent.venueid = venueidParts.join('/');
    }
    
    newContent._bibtex = dataToBibtex(data);
    newContent.authors = data.authors;
    newContent.authorids = data.authorids;
    if (data.url) {
      if (data.url.endsWith('.pdf')) {
        newContent.pdf = data.url;
      } else {
        newContent.html = data.url;
      }
    }
    
    note.cdate = data.cdate;
    note.pdate = new Date(data.year, 0, 1).getTime();
    note.content = newContent;
    note.content.title = data.title;
    return note;
  } else {
    throw "Something went wrong. No entryElement.";
  }
};