#!/bin/haserl
<%in _common.cgi %>
<%
plugin="record"
page_title="Video Recording"
params="blink debug diskusage duration enabled filename led loop mount videoformat"

# constants
MOUNTS=$(awk '/nfs|fat/{print $2}' /etc/mtab)
RECORD_CTL="/etc/init.d/S96record"

config_file="$ui_config_dir/$plugin.conf"
include $config_file

# defaults
[ -z "$record_blink" ] && record_blink=1
[ -z "$record_debug" ] && record_debug=true
[ -z "$record_diskusage" ] && record_diskusage=85
[ -z "$record_duration" ] && record_duration=60
[ -z "$record_enabled" ] && record_enabled="false"
[ -z "$record_led" ] && record_led=$(fw_printenv | awk -F= '/^gpio_led/{print $1;exit}')
[ -z "$record_loop" ] && record_loop="true"
[ -z "$record_videoformat" ] && record_videoformat="mp4"
if [ -z "$record_filename" ] || [ "/" = "${record_filename:0-1}" ]; then
	record_filename="thingino/%Y-%m-%d/%Y-%m-%dT%H-%M-%S"
fi

if [ "POST" = "$REQUEST_METHOD" ]; then
	# parse values from parameters
	read_from_post "$plugin" "$params"

	# normalize
	[ "/" = "${record_filename:0:1}" ] && record_filename="${record_filename:1}"

	# validate
	[ -z "$record_mount" ] && set_error_flag "Record mount cannot be empty."
	[ -z "$record_filename" ] && set_error_flag "Record filename cannot be empty."

	if [ -z "$error" ]; then
		tmp_file=$(mktemp)
		for p in $params; do
			echo "${plugin}_$p=\"$(eval echo \$${plugin}_$p)\"" >>$tmp_file
		done; unset p
		mv $tmp_file $config_file

		if [ -f "$RECORD_CTL" ]; then
			if [ "true" = "$record_enabled" ]; then
				$RECORD_CTL start > /dev/null
			else
				$RECORD_CTL stop > /dev/null
			fi
		fi

		update_caminfo
		redirect_to $SCRIPT_NAME
	fi
fi
%>
<%in _header.cgi %>

<form action="<%= $SCRIPT_NAME %>" method="post">
<% field_switch "record_enabled" "Enable Recording" %>
<div class="row row-cols-1 row-cols-lg-3 g-4 mb-4">
<div class="col">
<% field_select "record_mount" "Record storage directory" "$MOUNTS" %>
<div class="row g-1">
<div class="col-9"><% field_text "record_filename" "File name template" "$STR_SUPPORTS_STRFTIME" %></div>
<div class="col-3"><% field_select "record_videoformat" "Format" "mov, mp4" "also extention" %></div>
</div>
<% field_checkbox "record_loop" "Loop Recording" "Delete older files as needed." %>
</div>
<div class="col">
<% field_range "record_diskusage" "Total disk space usage limit, %" "5,95,5" %>
<% field_number "record_duration" "Recording duration per file, seconds" %>
</div>
<div class="col">
<% field_select "record_led" "Indicator LED" "$(fw_printenv | awk -F= '/^gpio_led/{print $1}')" %>
<% field_range "record_blink" "Blink interval, seconds" "0,3.0,0.5" "Set to 0 for always on"%>
</div>
</div>
<% button_submit %>
</form>

<br>
<% if pidof record > /dev/null; then %>
<h3 class="alert alert-info">Recording in progress.</h3>
<% else %>
<div class="alert alert-danger">
<h3>Recording stopped.</h3>
<p class="mb-0">Please note. The last active recording will continue until the end of the recording time!</p>
</div>
<% fi %>

<%in _footer.cgi %>
