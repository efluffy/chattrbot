#!/usr/bin/perl -wT 

use strict;
use CGI;
use LWP::UserAgent;
use JSON;
use Data::Dumper;

if($ENV{REMOTE_ADDR} !~ /149\.154\.(1(6[4-7]))\.([0-9]|[1-9][0-9]|1([0-9][0-9])|2([0-4][0-9]|5[0-5]))/) { print "Content-type: text/html\n\n"; exit(0); }

my $botid = "tg_bot_api_token";
my $gapi = "google_cloud_translate_api_key";

my $q;
my $json;
my $jsonres;
my %result;
my $queryid;
my $query;
my $trans;
my $ua;
my $res;
my $langto;

my $inlineReply = "https://api.telegram.org/bot$botid/answerInlineQuery";
my $googapi = "https://translation.googleapis.com/language/translate/v2";

$q = CGI->new;
print $q->header();
$json = decode_json( $q->param('POSTDATA') );

if(!defined($json->{inline_query}->{id})) { exit(0); }

$queryid = $json->{inline_query}->{id};
$query = $json->{inline_query}->{query};

$langto = (split /:/, $query)[0];
if(!defined($langto) || $langto !~ /(en|ru|de|ja|es|fr|zh)/ ) { exit(0); }

$query =~ s/^(en|ru|de|ja|es|fr|zh)://i;
if(!defined($query)) { exit(0); }

$ua = LWP::UserAgent->new( ssl_opts => { verify_hostname => 1 } );

if($query ne "") {
	$res = $ua->post($googapi, [
		"q" 		=> $query,
		"target" 	=> $langto,
		"format"	=> "text",
		"key"		=> $gapi
	]);
	$jsonres = decode_json($res->content);
	
	if(defined($jsonres->{error})) { die Dumper($jsonres); }
	
	$trans = $jsonres->{data}->{translations}[0]->{translatedText};
	
	if($trans ne "") {
		%result = (
			"type" 	=> "article",
			"id" 	=> "1",
			"title" => "Translation:",
			"description" => "$trans",
			"input_message_content" => {
				"message_text" => "$trans",
			},
		);
		
		$res = $ua->post($inlineReply, [
			"inline_query_id" => $queryid,
			"cache_time" => 1,
			"is_personal" => "true",
			"results" => to_json([\%result])
		]);
		
		if($res->code != 200) {
			open(my $fh, '>>', "debug.txt");
			my $dbgs = "SENT: " . "[\"inline_query_id\" => $queryid, \"results\" => ". to_json([\%result]) . "]\n";
			my $dbgr = "RECD: " . $res->code . ":" . $res->content . "\n";
			print $fh $dbgs;
			print $fh $dbgr;
			close($fh);
			die("telegram responded wrongly\n");
		}
	}
}

exit(0);