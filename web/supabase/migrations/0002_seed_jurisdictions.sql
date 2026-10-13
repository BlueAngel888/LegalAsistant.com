-- Starter legislation references. All rows are verified = false until a
-- lawyer confirms them (planned for Week 5). Add countries/types freely.

insert into jurisdiction_data (country_code, country_name, document_type, title, reference, summary) values
-- Romania
('RO', 'România', null,             'Codul civil',                         'Legea nr. 287/2009 privind Codul civil, republicată', 'Dreptul comun pentru obligații, contracte, răspundere civilă și prescripție.'),
('RO', 'România', null,             'Codul de procedură civilă',           'Legea nr. 134/2010 privind Codul de procedură civilă, republicată', 'Procedura în fața instanțelor civile, termene, căi de atac.'),
('RO', 'România', 'contract',       'Clauze abuzive în contractele cu consumatorii', 'Legea nr. 193/2000 privind clauzele abuzive din contractele încheiate între profesioniști și consumatori', 'Clauze nenegociate care creează un dezechilibru semnificativ în defavoarea consumatorului.'),
('RO', 'România', 'fine',           'Regimul juridic al contravențiilor',  'Ordonanța Guvernului nr. 2/2001 privind regimul juridic al contravențiilor', 'Conținutul obligatoriu al procesului-verbal, cauze de nulitate, termenul de 15 zile pentru plângere, plata a jumătate din minim în 15 zile.'),
('RO', 'România', 'fine',           'Circulația pe drumurile publice',     'OUG nr. 195/2002 privind circulația pe drumurile publice, republicată', 'Contravenții rutiere, puncte de penalizare, suspendarea permisului.'),
('RO', 'România', 'court_decision', 'Căi de atac',                         'Legea nr. 134/2010 (Codul de procedură civilă), Cartea a II-a, Titlul V', 'Apel, recurs, contestație în anulare, revizuire și termenele lor.'),
-- Germany
('DE', 'Deutschland', null,         'Bürgerliches Gesetzbuch',             'BGB', 'Allgemeines Zivilrecht, Schuldrecht, Verjährung.'),
('DE', 'Deutschland', 'contract',   'Allgemeine Geschäftsbedingungen',     'BGB §§ 305–310', 'Inhaltskontrolle von AGB, unangemessene Benachteiligung.'),
('DE', 'Deutschland', 'fine',       'Ordnungswidrigkeitengesetz',          'OWiG, insb. § 67 (Einspruch gegen den Bußgeldbescheid, 2 Wochen)', 'Bußgeldverfahren, Einspruch, Verjährung.'),
('DE', 'Deutschland', 'court_decision', 'Zivilprozessordnung',             'ZPO, Berufung §§ 511 ff.', 'Rechtsmittel und Fristen im Zivilprozess.'),
-- United Kingdom (England & Wales)
('GB', 'United Kingdom', 'contract','Consumer Rights Act 2015',            'Consumer Rights Act 2015, Part 2 (unfair terms)', 'Fairness test and transparency for consumer contract terms.'),
('GB', 'United Kingdom', 'contract','Unfair Contract Terms Act 1977',      'Unfair Contract Terms Act 1977', 'Limits on exclusion and limitation clauses in business contracts.'),
('GB', 'United Kingdom', 'fine',    'Road Traffic Offenders Act 1988',     'Road Traffic Offenders Act 1988, s.1 (notice of intended prosecution)', 'Notice requirements and time limits for road traffic offences.'),
('GB', 'United Kingdom', null,      'Limitation Act 1980',                 'Limitation Act 1980', 'Time limits for bringing civil claims.');
