//
// Copyright (c)2015, dblp Team (University of Trier and
// Schloss Dagstuhl - Leibniz-Zentrum fuer Informatik GmbH)
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// (1) Redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer.
//
// (2) Redistributions in binary form must reproduce the above copyright
// notice, this list of conditions and the following disclaimer in the
// documentation and/or other materials provided with the distribution.
//
// (3) Neither the name of the dblp team nor the names of its contributors
// may be used to endorse or promote products derived from this software
// without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL DBLP TEAM BE LIABLE FOR ANY
// DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.time.LocalDate;

import org.dblp.mmdb.Field;
import org.dblp.mmdb.Person;
import org.dblp.mmdb.PersonName;
import org.dblp.mmdb.Publication;
import org.dblp.mmdb.RecordDb;
import org.dblp.mmdb.RecordDbInterface;
import org.dblp.mmdb.TableOfContents;
import org.dblp.mmdb.Mmdb;
import org.xml.sax.SAXException;

import com.google.gson.Gson;
// import com.google.gson.GsonBuilder;

@SuppressWarnings("javadoc")
class DblpParser {

    public static void main(String[] args) {

        // we need to raise entityExpansionLimit because the dblp.xml has millions of
        // entities
        System.setProperty("entityExpansionLimit", "10000000");

        if (args.length != 3) {
            System.err.format("Usage: java %s <dblp-xml-file> <dblp-dtd-file> <last-retrieved-date>\n",
                    DblpParser.class.getName());
            System.exit(0);
        }
        String dblpXmlFilename = args[0];
        String dblpDtdFilename = args[1];
        LocalDate date = LocalDate.parse(args[2]);

        HashMap<String, List<String>> recentlyModifiedHashMap = new HashMap<String, List<String>>();

        System.out.println("building the dblp main memory DB ...");
        RecordDbInterface dblp;
        try {
            dblp = new RecordDb(dblpXmlFilename, dblpDtdFilename, false);
        } catch (final IOException ex) {
            System.err.println("cannot read dblp XML: " + ex.getMessage());
            return;
        } catch (final SAXException ex) {
            System.err.println("cannot parse XML: " + ex.getMessage());
            return;
        }
        System.out.format("MMDB ready: %d publs, %d pers\n\n", dblp.numberOfPublications(), dblp.numberOfPersons());

        System.out.println("Finding all publications modified after " + date.toString());
        Collection<Person> allPeople = dblp.getPersons();

        for (Person person : allPeople) {
            // get the latest mdate, if it is greater than the date we get, retrieve all
            // records for that person.
            LocalDate mDate = LocalDate.parse(person.getAggregatedMdate());
            if (mDate.equals(date) || mDate.isAfter(date)) {
                List<Publication> publications = person.getPublications();
                List<String> modifiedPublications = new ArrayList<String>();
                for (Publication p : publications) {
                    LocalDate publicationMDate = LocalDate.parse(p.getMdate());
                    if (publicationMDate.equals(date) || publicationMDate.isAfter(date)) {
                        modifiedPublications.add(p.getXml());
                    }
                }
                recentlyModifiedHashMap.put(person.getPid(), modifiedPublications);
            }
        }

        // System.out.println(recentlyModifiedHashMap.toString());

        String filePath = "data/recentlyModified.json";
        System.out.println("Writing publications modified after " + date.toString() + " to " + filePath);

        String jsonString = new Gson().toJson(recentlyModifiedHashMap);

        try (FileWriter file = new FileWriter(filePath)) {
            file.write(jsonString);
            System.out.println("Successfully wrote JSON string to file: " + filePath);
        } catch (IOException e) {
            e.printStackTrace();
        }

        System.out.println("done.");
    }
}