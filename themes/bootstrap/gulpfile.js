var gulp  = require('gulp'),
  sass = require('gulp-sass'),
  sourcemaps = require('gulp-sourcemaps'),
  cleanCss = require('gulp-clean-css'),
  rename = require('gulp-rename'),
  postcss      = require('gulp-postcss'),
  autoprefixer = require('autoprefixer');

gulp.task('build-theme', function() {
  return gulp.src(['scss/*.scss'])
    //.pipe(sourcemaps.init())
    .pipe(sass({
    outputStyle: "expanded",
    precision: 6
    }).on('error', sass.logError))
    .pipe(postcss([ autoprefixer({ browsers: [
    "last 1 major version",
    ">= 1%",
    "Chrome >= 45",
    "Firefox >= 38",
    "Edge >= 12",
    "Explorer >= 10",
    "iOS >= 9",
    "Safari >= 9",
    "Android >= 4.4",
    "Opera >= 30"]})]))
    //.pipe(sourcemaps.write('../maps'))
    .pipe(gulp.dest('css/'))
    .pipe(cleanCss())
    .pipe(rename({suffix: '.min'}))
    .pipe(gulp.dest('css/'))
});

gulp.task('watch', ['build-theme'], function() {
  gulp.watch(['scss/*.scss'], ['build-theme']);
});

gulp.task('default', ['build-theme'], function() {
});



