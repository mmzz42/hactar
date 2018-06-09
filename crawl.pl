#!/usr/bin/perl
# mmzz 2017
my $def_link_coll = "crawlsource$year";
my $def_runs_coll = "run$year";
my $def_articles_coll = "article$year";

my $MaxArtSize= 90000; #bytes

while (my $crawlfeed = $find->next) {
	my $u1 = URI->new($crawlfeed->{URL});
        my $feedID=clean(decode_utf8($crawlfeed->{site}."|".$crawlfeed->{name}));
        my $seedURL=clean(decode_utf8($u1));
        my $seedHash = md5_hex($seedURL);



	# GET homepage URL

	my $ratioFactor=500;

	my $uriValidator = new Data::Validate::URI();

	my ($seedh,$seedhost,$seedpath,$seedquery,$seedfragment) = validateUrl($seedURL);
	my $protocol;
	$seedURL =~m/^(\w+):/;
	$protocol=$1."://";

	my $internalLinks=0;
	my %seen;


	#SCRAPE URLs
	use HTML::TreeBuilder::XPath;
	my $root = HTML::TreeBuilder::XPath->new_from_content($artBody);

	my $urlxpath = '//a[@href]';
	my @urls;
	my $cnt;

	foreach my $node ($root->findnodes($urlxpath)){
		my $url = $node->attr('href') ;
		my $title = clean(decode_utf8($node->attr('title'))) ;
		my $urltext = clean(decode_utf8($node->as_text));

	#	print "$url -> ";
		my $uriValidator = new Data::Validate::URI();
		my ($h,$host,$path,$query,$fragment)=validateUrl($url);
		if ($host eq "") {
			$url=$protocol.$seedhost.$url;		
			my ($h,$host,$path,$query,$fragment)=validateUrl($url);
			if ($host eq "") {
				next;
			}
		}
		if ( $url=~m/^https?:\/\/$seedhost/ && $url ne "") {  #internal link
			push @urls, $url if ! $seen{"$url"}++;  #acts as uniq : http://www.perlmonks.org/?node_id=981329{
			$cnt++;
			$cntItm++;
		}
	}
	print STDOUT "$0 INFO CRAWL; $cnt urls collected from feed $feedID\n" ;
	my $acnt ;
	foreach (@urls) {
		my ($accept,$ratio,$articleBody)=pageratio($_,$ratioFactor) ;
		if ($accept) {
			savePage($_,$seedURL,$articleBody,$feedID);
			$acnt++
		} else {
			$DEBUG && print STDOUT "$0 INFO ITEM; ratio $ratio ;rejected item; $_\n" ;
			$cntRej++;
		}
	}
	my $accrate= $acnt/$cnt;
	my $rounded = $accrate *100;
	$rounded = sprintf "%02f", $accrate;

	print STDOUT "$0 INFO SOURCE; $acnt/$cnt ($rounded%) articles accepted from $feedID\n" ;
}

my $end=DateTime->now;
my $d = DateTime::Format::Duration->new(
              pattern => '%H hours, %M minutes, %S seconds'
        );
my $runDuration= $d->format_duration($end-$start);
        


print STDOUT "$0 INFO RUN; duration $runDuration; $cntItm links followed; $cntNew new articles inserted; $cntRej items rejected, $cntDup duplicates skipped\n";



##
## SUBS
##


# give the page a rank based on an euristic including: internal links, dashes in URL, url length and text lenght.
# the ratio discriminates pages containg the articles from pages linking to other articles (topics)
sub pageratio {
	my ($seedURL,$ratioFactor) = @_;


        my ($seedh,$seedhost,$seedpath,$seedquery,$seedfragment) = validateUrl($seedURL);
        my $protocol;
        $seedURL =~m/^(\w+):/;
        $protocol=$1."://";

        my $internalLinks=0;
        my $textLen=0;
        my $textLen300=0;
        my $urlLen=0;
        my $divcount=0;
        my $spancount=0;
        my $textcount=0;

        ### Create the user agent ###
        #resolve redirects
        my $ua = LWP::UserAgent->new;
        my $request  = HTTP::Request->new( GET => $seedURL);
        my $response = $ua->request($request);
        my $artRealURL = $seedURL;
        $artRealURL = $response->request->uri()->as_string ;
        my $artBody = $response->content;
        my $downloadTS=DateTime->now();

        #Body Cleanup
        my $text = scrubBody ($artBody);


        #SCRAPE URLs
        use HTML::TreeBuilder::XPath;
        my $root = HTML::TreeBuilder::XPath->new_from_content($artBody);

        my $urlxpath = '//a[@href]';
        my $textxpath="//*[(name() !='script') and (name()!='style') and ((p) or (a) or (div)) ]/node()/text()";
        my $textxpath300="//*[(name() !='script') and (name()!='style') and ((p) or (a) or (div)) ]/node()[(string-length() > 300)]/text()";

        foreach my $node ($root->findnodes($urlxpath)){
                my $url = $node->attr('href') ;
                my $title = clean(decode_utf8($node->attr('title'))) ;
                my $urltext = clean(decode_utf8($node->as_text));

                my $uriValidator = new Data::Validate::URI();
                my ($h,$host,$path,$query,$fragment)=validateUrl($url);
                if ($host eq "") {
                        $url=$protocol.$seedhost.$url;
                        my ($h,$host,$path,$query,$fragment)=validateUrl($url);
                        if ($host eq "") {
                                next;
                        }
                }
                if ( $url=~m/$seedhost/ && $url ne "") {  #internal link
                        $internalLinks++;
                }
        }

        foreach my $node ($text = $root->findnodes($textxpath)){
                $textLen+=length($text);
                $textcount++;
        }
        foreach my $node ($text = $root->findnodes($textxpath300)){
                $textLen300+=length($text);
        }
        $root -> delete;
        $seedURL=~s/\#.*$//;
        $seedURL=~s/\?.*$//;
        $seedURL=~s/#.*$//;

        $seedURL=~s/\s+$//;
        $seedURL=~m/^(.*:)\/\/([A-Za-z0-9\-\.]+)(:[0-9]+)?(.*)$/;
        my $path=$4;
        $urlLen=length($path);


        my $URLhasfrag=0;
        if ($seedURL =~ m/\?/) {
                $URLhasfrag++;
        }
        my $dashes = $seedURL =~ tr/-/-/;
        $dashes += $seedURL =~ tr/_/_/;

        my $ispage=0;
        if ($seedURL =~ m/html$/) {
                $ispage = 1;
        }

        my $ratio=0;
        if ($internalLinks) {
                $ratio=(($textLen/$internalLinks)*$urlLen*--$dashes)/$ratioFactor;
        }
	$ratio = $ratio -1;
	my $rounded = sprintf "%+.2f", $ratio;

        my $accept = 0;
        $accept = 1 if ($ratio > 0);


	return $accept,$rounded,$artBody ;
}

sub scrubBody {
	my $artBody = shift;
	     # insert Space et each HTML TAG end to avoid words sticking together
        $artBody =~ s/<\//\ <\//g;
        $artBody =~ s/<br>/ /g;
        $artBody =~ s/\n/ \n/g;

       # determine the proper charset for decoding, default to utf8
        use Encode;
        use Encode::HanExtra;
        use Encode::Unicode;
        use Encode::Byte;
        use Encode::Detect::Detector;
        my $charset = Encode::Detect::Detector::detect($artBody);
        if($charset) {
                eval(Encode::from_to($artBody,$charset,'utf8'));
        }
        my $berr = eval(utf8::decode($artBody));
# Do scrubbing
#CLEANUP
	use HTML::Scrubber;

	my @rules = (
	        script => 0,
	        a => {
	            alt => 1,                 # alt attribute allowed
	            '*' => 0,                 # deny all other attributes
	        },
	        img => {
	            alt => 1,                 # alt attribute allowed
	            '*' => 0,                 # deny all other attributes
	        },
	    );
	my    $scrubber = HTML::Scrubber->new(
	        allow   => qw[ a p b i u div]  ,
	        deny    => qw[ ol ul li h1 h2 h3 hr br ],
	        rules   => \@rules,
	        default => 1,
	        comment => 0,
	        process => 0,
	    );

        my $text= $scrubber->scrub($artBody);

        $text =~ s/<strong>//g;
        $text =~ s/<\/strong>//g;
        $text =~ s/<cite>//g;
        $text =~ s/<\/cite>//g;
        $text =~ s/<a>//g;
        $text =~ s/<\/a>//g;
        $text =~ s/<u>//g;
        $text =~ s/<\/u>//g;
        $text =~ s/<p>/ /g;
        $text =~ s/<\/p>/ /g;

	return($text);

}





sub validateUrl {
	my $url = shift;
	my $uriValidator = new Data::Validate::URI();
	if ($uriValidator->is_web_uri($url)){
        	my $h = URI->new($url)->canonical;
        	my $host= $h->host;
        	my $path= $h->path;
 		my $query= $h->query;
       		my $fragment = $h->fragment;
		return ($h,$host,$path,$query,$fragment);
	} else  {
		return ("","","","","");
}

}
sub clean {
        my $text = shift;
        #replace newlines, cr with blank
        $text =~ s/\n/ /g;
        $text =~ s/\r/ /g;
        #remove trailing & leading blanks
        $text =~ s/^\s+//;
        $text =~ s/\s+$//;
        return $text;
}

sub get_checksum {
        my $tent = md5_hex(encode_utf8($_[0]));
        $tent =~ s/\W/_/g;
        return $tent;
}

