# Aurelius - Deleted Files Log

> **"Shaping Tomorrow's Leaders Today"**

This document lists all files deleted during the Aurelius project cleanup on January 6, 2026.

---

## Summary

| Category | Count |
|----------|-------|
| Redundant Docker Files | 7 |
| Historical Documentation | 6 |
| W3 CRM Template Files | 442 |
| **Total** | **455** |

---

## 1. Redundant Docker Files (7 files)

These files were duplicates of files already in the `docker/` folder:

```
Dockerfile                  # Duplicate of docker/development/Dockerfile
Dockerfile.prod             # Duplicate of docker/production/Dockerfile
docker-compose.yml          # Redundant - consolidated into dev/prod files
docker-compose.prod.yml     # Duplicate of docker-compose-prod.yml
compose.yaml                # Outdated - referenced wrong project name
docker-entrypoint.sh        # Duplicate of docker/development/docker-entrypoint-dev.sh
README.Docker.md            # Content already in docker/README.md
```

---

## 2. Historical Documentation (6 files)

These were historical completion reports no longer needed:

```
IMPLEMENTATION_COMPLETE.md
COMPLETE_IMPLEMENTATION.md
FINAL_STATUS.md
PHASE2_COMPLETION_REPORT.md
PHASE3_COMPLETION_REPORT.md
DOCKER_AUTOMATION_SUMMARY.md
```

---

## 3. W3 CRM Template Files (442 files)

The W3 CRM folder was an unused admin template that was not part of the School Management System.

### HTML Pages (94 files)

```
W3 CRM/@yaireo/tagify/index.html
W3 CRM/Edge/index-2.html
W3 CRM/Edge/index.html
W3 CRM/Trident/index.html
W3 CRM/account/activity.html
W3 CRM/account/api-keys.html
W3 CRM/account/billing.html
W3 CRM/account/logs.html
W3 CRM/account/overview.html
W3 CRM/account/referrals.html
W3 CRM/account/security.html
W3 CRM/account/settings.html
W3 CRM/account/statements.html
W3 CRM/add-blog.html
W3 CRM/add-email.html
W3 CRM/add-role.html
W3 CRM/app-calender.html
W3 CRM/app-profile-1.html
W3 CRM/app-profile-2.html
W3 CRM/app-profile.html
W3 CRM/applewebkit/index.html
W3 CRM/auto-write.html
W3 CRM/blog-1.html
W3 CRM/blog-category.html
W3 CRM/blog.html
W3 CRM/chart-chartist.html
W3 CRM/chart-chartjs.html
W3 CRM/chart-flot.html
W3 CRM/chart-morris.html
W3 CRM/chart-peity.html
W3 CRM/chart-sparkline.html
W3 CRM/chat.html
W3 CRM/chatbot.html
W3 CRM/chrome/index.html
W3 CRM/contacts.html
W3 CRM/content-add.html
W3 CRM/content.html
W3 CRM/core-hr.html
W3 CRM/customer-profile.html
W3 CRM/customer.html
W3 CRM/ecom-checkout.html
W3 CRM/ecom-customers.html
W3 CRM/ecom-invoice.html
W3 CRM/ecom-product-detail.html
W3 CRM/ecom-product-grid.html
W3 CRM/ecom-product-list.html
W3 CRM/ecom-product-order.html
W3 CRM/edit-profile.html
W3 CRM/email-compose.html
W3 CRM/email-inbox.html
W3 CRM/email-read.html
W3 CRM/email-template.html
W3 CRM/employee.html
W3 CRM/empty-page.html
W3 CRM/finance.html
W3 CRM/fine-tune-models.html
W3 CRM/form-ckeditor.html
W3 CRM/form-element.html
W3 CRM/form-pickers.html
W3 CRM/form-validation.html
W3 CRM/form-wizard.html
W3 CRM/import.html
W3 CRM/index-2.html
W3 CRM/index.html
W3 CRM/manage-client.html
W3 CRM/map-jqvmap.html
W3 CRM/menu.html
W3 CRM/page-error-400.html
W3 CRM/page-error-403.html
W3 CRM/page-error-404.html
W3 CRM/page-error-500.html
W3 CRM/page-error-503.html
W3 CRM/page-forgot-password.html
W3 CRM/page-lock-screen.html
W3 CRM/page-login.html
W3 CRM/page-register.html
W3 CRM/performance.html
W3 CRM/post-details.html
W3 CRM/profile/activity.html
W3 CRM/profile/campaigns.html
W3 CRM/profile/documents.html
W3 CRM/profile/followers.html
W3 CRM/profile/overview.html
W3 CRM/profile/projects-details.html
W3 CRM/profile/projects.html
W3 CRM/project.html
W3 CRM/prompt.html
W3 CRM/reports.html
W3 CRM/repurpose.html
W3 CRM/rss.html
W3 CRM/scheduled.html
W3 CRM/setting.html
W3 CRM/svg-icon.html
W3 CRM/table-bootstrap-basic.html
W3 CRM/table-datatable-basic.html
W3 CRM/task-summary.html
W3 CRM/task.html
W3 CRM/uc-lightgallery.html
W3 CRM/uc-nestable.html
W3 CRM/uc-noui-slider.html
W3 CRM/uc-select2.html
W3 CRM/uc-sweetalert.html
W3 CRM/uc-toastr.html
W3 CRM/ui-accordion.html
W3 CRM/ui-alert.html
W3 CRM/ui-badge.html
W3 CRM/ui-button-group.html
W3 CRM/ui-button.html
W3 CRM/ui-card.html
W3 CRM/ui-carousel.html
W3 CRM/ui-dropdown.html
W3 CRM/ui-grid.html
W3 CRM/ui-list-group.html
W3 CRM/ui-modal.html
W3 CRM/ui-pagination.html
W3 CRM/ui-popover.html
W3 CRM/ui-progressbar.html
W3 CRM/ui-tab.html
W3 CRM/ui-typography.html
W3 CRM/user-roles.html
W3 CRM/user.html
W3 CRM/widget-basic.html
```

### CSS Files (35 files)

```
W3 CRM/css/style.css
W3 CRM/icons/avasta/css/style.css
W3 CRM/icons/bootstrap-icons/font/bootstrap-icons.css
W3 CRM/icons/fontawesome/css/all.min.css
W3 CRM/icons/fontawesome6/css/all.min.css
W3 CRM/icons/icomoon/icomoon.css
W3 CRM/icons/line-awesome/css/line-awesome.min.css
W3 CRM/icons/material-design-iconic-font/css/materialdesignicons.min.css
W3 CRM/icons/simple-line-icons/css/simple-line-icons.css
W3 CRM/icons/themify-icons/css/themify-icons.css
W3 CRM/vendor/bootstrap-datepicker-master/css/bootstrap-datepicker.min.css
W3 CRM/vendor/bootstrap-daterangepicker/daterangepicker.css
W3 CRM/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css
W3 CRM/vendor/bootstrap-material-datetimepicker/css/bootstrap-material-datetimepicker.css
W3 CRM/vendor/chartist/css/chartist.min.css
W3 CRM/vendor/clockpicker/css/bootstrap-clockpicker.min.css
W3 CRM/vendor/datatables/css/jquery.dataTables.min.css
W3 CRM/vendor/fullcalendar/css/main.min.css
W3 CRM/vendor/jquery-asColorPicker/css/asColorPicker.min.css
W3 CRM/vendor/jqvmap/css/jqvmap.min.css
W3 CRM/vendor/jvmap/jquery-jvectormap.css
W3 CRM/vendor/lightgallery/css/lightgallery.min.css
W3 CRM/vendor/metismenu/css/metisMenu.min.css
W3 CRM/vendor/nestable2/css/jquery.nestable.min.css
W3 CRM/vendor/nouislider/nouislider.min.css
W3 CRM/vendor/perfect-scrollbar/css/perfect-scrollbar.css
W3 CRM/vendor/pickadate/themes/default.css
W3 CRM/vendor/pickadate/themes/default.date.css
W3 CRM/vendor/select2/css/select2.min.css
W3 CRM/vendor/star-rating/star-rating-svg.css
W3 CRM/vendor/swiper/css/swiper-bundle.min.css
W3 CRM/vendor/toastr/css/toastr.min.css
```

### JavaScript Files (55 files)

```
W3 CRM/js/custom.js
W3 CRM/js/dashboard/cms.js
W3 CRM/js/dashboard/core-hr.js
W3 CRM/js/dashboard/dashboard-1.js
W3 CRM/js/demo.js
W3 CRM/js/deznav-init.js
W3 CRM/js/highlight.min.js
W3 CRM/js/plugins-init/bs-daterange-picker-init.js
W3 CRM/js/plugins-init/chartist-init.js
W3 CRM/js/plugins-init/chartjs-init.js
W3 CRM/js/plugins-init/clock-picker-init.js
W3 CRM/js/plugins-init/datatables.init.js
W3 CRM/js/plugins-init/flot-init.js
W3 CRM/js/plugins-init/fullcalendar-init.js
W3 CRM/js/plugins-init/jquery-asColorPicker.init.js
W3 CRM/js/plugins-init/jquery.validate-init.js
W3 CRM/js/plugins-init/jqvmap-init.js
W3 CRM/js/plugins-init/material-date-picker-init.js
W3 CRM/js/plugins-init/morris-init.js
W3 CRM/js/plugins-init/nestable-init.js
W3 CRM/js/plugins-init/nouislider-init.js
W3 CRM/js/plugins-init/pickadate-init.js
W3 CRM/js/plugins-init/piety-init.js
W3 CRM/js/plugins-init/select2-init.js
W3 CRM/js/plugins-init/sparkline-init.js
W3 CRM/js/plugins-init/sweetalert.init.js
W3 CRM/js/plugins-init/toastr-init.js
W3 CRM/js/plugins-init/widgets-script-init.js
W3 CRM/js/styleSwitcher.js
W3 CRM/vendor/apexchart/apexchart.js
W3 CRM/vendor/bootstrap-datepicker-master/js/bootstrap-datepicker.min.js
W3 CRM/vendor/bootstrap-daterangepicker/daterangepicker.js
W3 CRM/vendor/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js
W3 CRM/vendor/bootstrap-datetimepicker/js/moment.js
W3 CRM/vendor/bootstrap-material-datetimepicker/js/bootstrap-material-datetimepicker.js
W3 CRM/vendor/chart.js/Chart.bundle.min.js
W3 CRM/vendor/chartist-plugin-tooltips/js/chartist-plugin-tooltip.min.js
W3 CRM/vendor/chartist/js/chartist.min.js
W3 CRM/vendor/ckeditor/ckeditor.js
W3 CRM/vendor/clockpicker/js/bootstrap-clockpicker.min.js
W3 CRM/vendor/datatables/js/buttons.html5.min.js
W3 CRM/vendor/datatables/js/dataTables.buttons.min.js
W3 CRM/vendor/datatables/js/jquery.dataTables.min.js
W3 CRM/vendor/datatables/js/jszip.min.js
W3 CRM/vendor/deznav/deznav.min.js
W3 CRM/vendor/draggable/draggable.js
W3 CRM/vendor/flot-spline/jquery.flot.spline.min.js
W3 CRM/vendor/flot/jquery.flot.js
W3 CRM/vendor/flot/jquery.flot.pie.js
W3 CRM/vendor/flot/jquery.flot.resize.js
W3 CRM/vendor/fullcalendar/js/main.min.js
W3 CRM/vendor/global/global.min.js
W3 CRM/vendor/highlightjs/highlight.pack.min.js
W3 CRM/vendor/jquery-asColor/jquery-asColor.min.js
W3 CRM/vendor/jquery-asColorPicker/js/jquery-asColorPicker.min.js
W3 CRM/vendor/jquery-asGradient/jquery-asGradient.min.js
W3 CRM/vendor/jquery-nice-select/js/jquery.nice-select.min.js
W3 CRM/vendor/jquery-sparkline/jquery.sparkline.min.js
W3 CRM/vendor/jquery-validation/jquery.validate.min.js
W3 CRM/vendor/jqvmap/js/jquery.vmap.min.js
W3 CRM/vendor/jqvmap/js/jquery.vmap.usa.js
W3 CRM/vendor/jqvmap/js/jquery.vmap.world.js
W3 CRM/vendor/lightgallery/js/lightgallery-all.min.js
W3 CRM/vendor/moment/moment.min.js
W3 CRM/vendor/morris/morris.min.js
W3 CRM/vendor/nestable2/js/jquery.nestable.min.js
W3 CRM/vendor/nouislider/nouislider.min.js
W3 CRM/vendor/peity/jquery.peity.min.js
W3 CRM/vendor/pickadate/picker.date.js
W3 CRM/vendor/pickadate/picker.js
W3 CRM/vendor/pickadate/picker.time.js
W3 CRM/vendor/raphael/raphael.min.js
W3 CRM/vendor/select2/js/select2.full.min.js
W3 CRM/vendor/star-rating/jquery.star-rating-svg.js
W3 CRM/vendor/svganimation/svg.animation.js
W3 CRM/vendor/svganimation/vivus.min.js
W3 CRM/vendor/toastr/js/toastr.min.js
W3 CRM/vendor/wnumb/wNumb.js
```

### Icon Fonts (74 files)

```
W3 CRM/icons/avasta/fonts/avasta.eot
W3 CRM/icons/avasta/fonts/avasta.svg
W3 CRM/icons/avasta/fonts/avasta.ttf
W3 CRM/icons/avasta/fonts/avasta.woff
W3 CRM/icons/avasta/fonts/avasta.woff2
W3 CRM/icons/bootstrap-icons/font/fonts/bootstrap-iconse36a.woff
W3 CRM/icons/bootstrap-icons/font/fonts/bootstrap-iconse36a.woff2
W3 CRM/icons/fontawesome/webfonts/fa-brands-400.ttf
W3 CRM/icons/fontawesome/webfonts/fa-brands-400.woff2
W3 CRM/icons/fontawesome/webfonts/fa-regular-400.ttf
W3 CRM/icons/fontawesome/webfonts/fa-regular-400.woff2
W3 CRM/icons/fontawesome/webfonts/fa-solid-900.ttf
W3 CRM/icons/fontawesome/webfonts/fa-solid-900.woff2
W3 CRM/icons/fontawesome/webfonts/fa-v4compatibility.ttf
W3 CRM/icons/fontawesome/webfonts/fa-v4compatibility.woff2
W3 CRM/icons/fontawesome6/webfonts/fa-brands-400.ttf
W3 CRM/icons/fontawesome6/webfonts/fa-brands-400.woff2
W3 CRM/icons/fontawesome6/webfonts/fa-regular-400.ttf
W3 CRM/icons/fontawesome6/webfonts/fa-regular-400.woff2
W3 CRM/icons/fontawesome6/webfonts/fa-solid-900.ttf
W3 CRM/icons/fontawesome6/webfonts/fa-solid-900.woff2
W3 CRM/icons/fontawesome6/webfonts/fa-v4compatibility.ttf
W3 CRM/icons/fontawesome6/webfonts/fa-v4compatibility.woff2
W3 CRM/icons/icomoon/fonts/icomoon.eot
W3 CRM/icons/icomoon/fonts/icomoon.svg
W3 CRM/icons/icomoon/fonts/icomoon.svg.readme
W3 CRM/icons/icomoon/fonts/icomoon.ttf
W3 CRM/icons/icomoon/fonts/icomoon.woff
W3 CRM/icons/line-awesome/fonts/la-brands-400.eot
W3 CRM/icons/line-awesome/fonts/la-brands-400.svg
W3 CRM/icons/line-awesome/fonts/la-brands-400.ttf
W3 CRM/icons/line-awesome/fonts/la-brands-400.woff
W3 CRM/icons/line-awesome/fonts/la-brands-400.woff2
W3 CRM/icons/line-awesome/fonts/la-brands-400d41d.eot
W3 CRM/icons/line-awesome/fonts/la-regular-400.eot
W3 CRM/icons/line-awesome/fonts/la-regular-400.svg
W3 CRM/icons/line-awesome/fonts/la-regular-400.ttf
W3 CRM/icons/line-awesome/fonts/la-regular-400.woff
W3 CRM/icons/line-awesome/fonts/la-regular-400.woff2
W3 CRM/icons/line-awesome/fonts/la-regular-400d41d.eot
W3 CRM/icons/line-awesome/fonts/la-solid-900.eot
W3 CRM/icons/line-awesome/fonts/la-solid-900.svg
W3 CRM/icons/line-awesome/fonts/la-solid-900.ttf
W3 CRM/icons/line-awesome/fonts/la-solid-900.woff
W3 CRM/icons/line-awesome/fonts/la-solid-900.woff2
W3 CRM/icons/line-awesome/fonts/la-solid-900d41d.eot
W3 CRM/icons/material-design-iconic-font/fonts/materialdesignicons-webfont683c.eot
W3 CRM/icons/material-design-iconic-font/fonts/materialdesignicons-webfont683c.svg
W3 CRM/icons/material-design-iconic-font/fonts/materialdesignicons-webfont683c.ttf
W3 CRM/icons/material-design-iconic-font/fonts/materialdesignicons-webfont683c.woff
W3 CRM/icons/material-design-iconic-font/fonts/materialdesignicons-webfont683c.woff2
W3 CRM/icons/material-design-iconic-font/fonts/materialdesignicons-webfontd41d.eot
W3 CRM/icons/simple-line-icons/fonts/Simple-Line-Icons4c824c82.eot
W3 CRM/icons/simple-line-icons/fonts/Simple-Line-Icons4c824c82.svg
W3 CRM/icons/simple-line-icons/fonts/Simple-Line-Icons4c824c82.ttf
W3 CRM/icons/simple-line-icons/fonts/Simple-Line-Icons4c824c82.woff
W3 CRM/icons/simple-line-icons/fonts/Simple-Line-Icons4c824c82.woff2
W3 CRM/icons/simple-line-icons/fonts/Simple-Line-Iconsd41dd41d.eot
W3 CRM/icons/themify-icons/fonts/themify.ttf
W3 CRM/icons/themify-icons/fonts/themify.woff
W3 CRM/icons/themify-icons/fonts/themify9f249f24.eot
W3 CRM/icons/themify-icons/fonts/themify9f249f24.svg
W3 CRM/icons/themify-icons/fonts/themifyd41dd41d.eot
W3 CRM/vendor/lightgallery/fonts/lgd41d.eot
W3 CRM/vendor/lightgallery/fonts/lgd641.eot
W3 CRM/vendor/lightgallery/fonts/lgd641.svg
W3 CRM/vendor/lightgallery/fonts/lgd641.ttf
W3 CRM/vendor/lightgallery/fonts/lgd641.woff
```

### Images (184 files)

```
W3 CRM/images/avatar/1.jpg
W3 CRM/images/avatar/1.png
W3 CRM/images/avatar/2.jpg
W3 CRM/images/avatar/3.jpg
W3 CRM/images/avatar/4.jpg
W3 CRM/images/avatar/5.jpg
W3 CRM/images/avatar/5.png
W3 CRM/images/big/img1.jpg
W3 CRM/images/big/img2.jpg
W3 CRM/images/big/img3.jpg
W3 CRM/images/big/img4.jpg
W3 CRM/images/big/img5.jpg
W3 CRM/images/big/img6.jpg
W3 CRM/images/big/img7.jpg
W3 CRM/images/big/img8.jpg
W3 CRM/images/blog/professional.jpg
W3 CRM/images/blog/professional2.jpg
W3 CRM/images/blog/s1.jpg
W3 CRM/images/blog/s2.jpg
W3 CRM/images/blog/s3.jpg
W3 CRM/images/blog/s4.jpg
W3 CRM/images/blog/s5.jpg
W3 CRM/images/blog/s6.jpg
W3 CRM/images/books.png
W3 CRM/images/card/1.png
W3 CRM/images/card/2.png
W3 CRM/images/card/3.png
W3 CRM/images/chat/1.png
W3 CRM/images/chat/2.png
W3 CRM/images/chat/3.png
W3 CRM/images/chat/4.png
W3 CRM/images/chat/5.png
W3 CRM/images/chat/google-docs1.png
W3 CRM/images/chat/music-notes1.png
W3 CRM/images/chat/pdf.png
W3 CRM/images/chat/play-button1.png
W3 CRM/images/contacts/d1.jpg
W3 CRM/images/contacts/d10.jpg
W3 CRM/images/contacts/d11.jpg
W3 CRM/images/contacts/d12.jpg
W3 CRM/images/contacts/d13.jpg
W3 CRM/images/contacts/d14.jpg
W3 CRM/images/contacts/d2.jpg
W3 CRM/images/contacts/d3.jpg
W3 CRM/images/contacts/d4.jpg
W3 CRM/images/contacts/d5.jpg
W3 CRM/images/contacts/d6.jpg
W3 CRM/images/contacts/d7.jpg
W3 CRM/images/contacts/d8.jpg
W3 CRM/images/contacts/d9.jpg
W3 CRM/images/contacts/pic1.jpg
W3 CRM/images/contacts/pic2.jpg
W3 CRM/images/contacts/pic3.jpg
W3 CRM/images/contacts/pic555.jpg
W3 CRM/images/contacts/pic666.jpg
W3 CRM/images/contacts/pic777.jpg
W3 CRM/images/contacts/pic888.jpg
W3 CRM/images/contacts/pic999.jpg
W3 CRM/images/country/aus.png
W3 CRM/images/country/canada.png
W3 CRM/images/country/china.png
W3 CRM/images/country/germany.png
W3 CRM/images/country/india.png
W3 CRM/images/country/pak.png
W3 CRM/images/country/russia.png
W3 CRM/images/country/uae.png
W3 CRM/images/country/uk.png
W3 CRM/images/country/usa.png
W3 CRM/images/credit.png
W3 CRM/images/crm-profile.jpg
W3 CRM/images/economics.png
W3 CRM/images/favicon.png
W3 CRM/images/file.png
W3 CRM/images/heart.png
W3 CRM/images/like.png
W3 CRM/images/logi-white.png
W3 CRM/images/login.png
W3 CRM/images/logo-full.png
W3 CRM/images/news.png
W3 CRM/images/no-img-avatar.png
W3 CRM/images/pattern/pattern5.png
W3 CRM/images/post/post1.jpg
W3 CRM/images/post/post11.jpg
W3 CRM/images/post/post12.jpg
W3 CRM/images/post/post13.jpg
W3 CRM/images/post/post2.jpg
W3 CRM/images/product/1.jpg
W3 CRM/images/product/2.jpg
W3 CRM/images/product/3.jpg
W3 CRM/images/product/4.jpg
W3 CRM/images/product/5.jpg
W3 CRM/images/product/6.jpg
W3 CRM/images/product/7.jpg
W3 CRM/images/profile/1.jpg
W3 CRM/images/profile/12.jpg
W3 CRM/images/profile/2.jpg
W3 CRM/images/profile/3.jpg
W3 CRM/images/profile/4.jpg
W3 CRM/images/profile/5.jpg
W3 CRM/images/profile/6.jpg
W3 CRM/images/profile/7.jpg
W3 CRM/images/profile/8.jpg
W3 CRM/images/profile/9.jpg
W3 CRM/images/profile/cover.jpg
W3 CRM/images/profile/friends/f1.jpg
W3 CRM/images/profile/friends/f2.jpg
W3 CRM/images/profile/friends/f3.jpg
W3 CRM/images/profile/friends/f4.jpg
W3 CRM/images/profile/profile.png
W3 CRM/images/profile/small/pic1.jpg
W3 CRM/images/profile/small/pic10.jpg
W3 CRM/images/profile/small/pic2.jpg
W3 CRM/images/profile/small/pic3.jpg
W3 CRM/images/profile/small/pic4.jpg
W3 CRM/images/profile/small/pic5.jpg
W3 CRM/images/profile/small/pic6.jpg
W3 CRM/images/profile/small/pic7.jpg
W3 CRM/images/profile/small/pic8.jpg
W3 CRM/images/profile/small/pic9.jpg
W3 CRM/images/qr.png
W3 CRM/images/svg/england.svg
W3 CRM/images/svg/india.svg
W3 CRM/images/svg/united-arab-emirates.svg
W3 CRM/images/tab/1.jpg
W3 CRM/images/tab/2.jpg
W3 CRM/images/tab/3.jpg
W3 CRM/images/tab/4.jpg
W3 CRM/images/user1.jpg
W3 CRM/social-image.png
W3 CRM/vendor/datatables/images/sort_asc.png
W3 CRM/vendor/datatables/images/sort_asc_disabled.png
W3 CRM/vendor/datatables/images/sort_both.png
W3 CRM/vendor/datatables/images/sort_desc.png
W3 CRM/vendor/datatables/images/sort_desc_disabled.png
W3 CRM/vendor/jquery-asColorPicker/images/alpha.png
W3 CRM/vendor/jquery-asColorPicker/images/hue.png
W3 CRM/vendor/jquery-asColorPicker/images/saturation.png
W3 CRM/vendor/jquery-asColorPicker/images/transparent.png
W3 CRM/vendor/lightgallery/img/loading.gif
W3 CRM/vendor/lightgallery/img/video-play.png
W3 CRM/vendor/lightgallery/img/vimeo-play.png
W3 CRM/vendor/lightgallery/img/youtube-play.png
```

---

## Files Moved (Not Deleted)

The following files were moved to new locations, not deleted:

### Documentation (moved to docs/)
- API.md
- DEPLOYMENT.md
- DOCKER_DEPLOYMENT.md
- IMPLEMENTATION_GUIDE.md
- PROJECT_STATUS.md
- QUICK_START.md
- SECURITY.md
- TODO.md

### Scripts (moved to scripts/)
- deploy.sh
- download_assets.sh
- create_superuser_if_none.py
- wait_for_db.py
- verify_system.py
