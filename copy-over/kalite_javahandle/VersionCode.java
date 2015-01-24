package org.kalite_javahandle;

import org.renpy.android.PythonActivity;
import android.app.Activity;

import android.widget.Toast;

import android.content.SharedPreferences;
import android.content.SharedPreferences.Editor;

import android.content.pm.PackageInfo;
import android.content.pm.PackageManager.NameNotFoundException;
import android.content.pm.PackageManager;

public class VersionCode {
	static Activity myActivity = (Activity)PythonActivity.mActivity;
	SharedPreferences sharedpreferences;
	Editor editor;

	public boolean matched_version(){
		sharedpreferences = myActivity.getSharedPreferences("MyPref", myActivity.MODE_MULTI_PROCESS);
		if(get_app_version() != sharedpreferences.getInt("version_code", 0)){
			return false;
		}else{
			return true;
		}
	}

	public int get_app_version(){
		String packname = myActivity.getPackageName();
		int ver = -1;
		try {
		    PackageInfo info = myActivity.getPackageManager().getPackageInfo(packname, 0);
		    ver = info.versionCode;
		} catch (NameNotFoundException e) {
		} 
		return ver;
	}

}