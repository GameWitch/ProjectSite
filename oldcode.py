g_maps = googlemaps.Client("AIzaSyANp7sVncdFiSj4-DJBrqIZLxPAumlBju8")

def query_to_list_of_dicts(query_object):
    list_of_dicts = []
    for obj in query_object:
        list_of_dicts.append(obj.to_dict())
    return list_of_dicts


def geocode():
    # just need to run this for every object in Address table and change the long and lat properties to whatever this shit says
    all_addresses = Address.query.all()
    g_success = 0
    g_failed = 0
    o_success = 0
    o_failed = 0
    for addy in all_addresses:
        address = addy.get_property_address()
        g = g_maps.geocode(address)
        if len(g) != 0:
            g_success += 1
            lattitude = g[0]["geometry"]["location"]["lat"]
            longitude = g[0]["geometry"]["location"]["lng"]
        else:
            g_failed += 1
            url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(address) + '?format=json'
            response = requests.get(url).json()
            if len(response) != 0:
                o_success += 1
                lattitude = response[0]['lat']
                longitude = response[0]['lon']
            else:
                o_failed += 1
                lattitude = ""
                longitude = ""
        addy.site_lat = lattitude
        addy.site_long = longitude
        db.session.commit()
    print(f"google success: {g_success}")
    print(f"google failed: {g_failed}")
    print(f"openmaps success: {o_success}")
    print(f"openmaps failed: {o_failed}")



def make_address_location_xcel():
    data = pandas.read_excel('March2022.xlsx')
    properties = data.to_dict('records')
    dict_of_lists = {}
    dict_of_lists["address"] = []
    dict_of_lists["lattitude"] = []
    dict_of_lists['longitude'] = []
    for prop in properties:
        for key in prop.keys():
            if prop[key] is None:
                prop[key] = ""
            if pandas.isna(prop[key]):
                prop[key] = ""
        site_nbr = prop["SITE_NBR"]
        if type(site_nbr) == float:
            site_nbr = str(int(prop["SITE_NBR"]))
        address = " ".join([site_nbr, prop["SITE_DIR"], prop["SITE_NAME"], prop["SITE_MODE"]])
        dict_of_lists["address"].append(address)
        dict_of_lists["lattitude"].append(prop["site_lat"])
        dict_of_lists["longitude"].append(prop["site_long"])
    dataframe = pandas.DataFrame.from_dict(dict_of_lists)
    dataframe.to_excel('addresslocations.xlsx')


def load_db_to_xl():
    dict_of_dicts = {}
    headers = Address.query.first().to_dict()
    for key in headers.keys():
        column = []
        dict_of_dicts[key] = column
    all_addresses = Address.query.all()
    for address in all_addresses:
        addy = address.to_dict()
        for column_key in dict_of_dicts.keys():
            dict_of_dicts[column_key].append(addy[column_key])
    data = pandas.DataFrame.from_dict(dict_of_dicts)
    today = datetime.now()
    filename = today.strftime("%B") + today.strftime("%Y")
    data.to_excel(f'{filename}.xlsx')


def load_locations():
    data = pandas.read_excel('addresslocations.xlsx')

    properties = data.to_dict('records')
    for record in properties:
        for key in record:
            if record[key] is None:
                record[key] = ""
            elif pandas.isna(record[key]):
                record[key] = ""
        location = Location(address=record["address"],
                            lattitude=record["lattitude"],
                            longitude=record["longitude"]
                            )
        db.session.add(location)
    db.session.commit()
    print("done")


def load_xl_into_db(excel_file):
    data = pandas.read_excel(excel_file)
    properties = data.to_dict('records')
    for property_entry in properties:
        for key in property_entry:
            if property_entry[key] is None:
                property_entry[key] = ""
            elif pandas.isna(property_entry[key]):
                property_entry[key] = ""
        if type(property_entry['OWNER_NUM']) == float:
            owner_number = str(int(property_entry['OWNER_NUM']))
        else:
            owner_number = property_entry['OWNER_NUM']
        if type(property_entry['SITE_NBR']) == float:
            site_number = str(int(property_entry['SITE_NBR']))
        else:
            site_number = property_entry['SITE_NBR']
        address = Address(owner=property_entry['OWNER'],
                          co_owner=property_entry['CO_OWNER'],
                          owner_num=owner_number,
                          owner_dir=property_entry['OWNER_DIR'],
                          owner_st=property_entry['OWNER_ST'],
                          owner_st_type=property_entry['OWNER_TYPE'],
                          owner_apt=property_entry['OWNER_APT'],
                          owner_city=property_entry['OWNER_CITY'],
                          owner_state=property_entry['OWNER_STATE'],
                          owner_zip=property_entry['OWNER_ZIP'],
                          site_number=site_number,
                          site_dir=property_entry['SITE_DIR'],
                          site_name=property_entry['SITE_NAME'],
                          site_st_type=property_entry['SITE_MODE'],
                          site_more=property_entry['SITE_MORE'],
                          property_value=property_entry['TOTAL_VALUE'],
                          property_taxes=property_entry['ASMT_TAXABLE'],
                          taxes_exempt=property_entry['ASMT_EXEMPT_AMT'],
                          )
        db.session.add(address)
    db.session.commit()
    print("done building data")


def delete_all_addresses():
    addresses = db.session.query(Address).all()
    for addy in addresses:
        db.session.delete(addy)
    db.session.commit()
    print("done deletin")


class Address(db.Model):
    __tablename__ = "addresses"
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.String(100), nullable=True)
    co_owner = db.Column(db.String(100), nullable=True)
    owner_num = db.Column(db.String(100))
    owner_dir = db.Column(db.String(10))
    owner_st = db.Column(db.String(100))
    owner_st_type = db.Column(db.String(100))
    owner_apt = db.Column(db.String(100))
    owner_city = db.Column(db.String(100))
    owner_state = db.Column(db.String(100))
    owner_zip = db.Column(db.String(100))
    site_number = db.Column(db.String(100))
    site_dir = db.Column(db.String(100))
    site_name = db.Column(db.String(100))
    site_st_type = db.Column(db.String(100))
    site_more = db.Column(db.String(100))
    site_long = db.Column(db.String(100))
    site_lat = db.Column(db.String(100))
    property_value = db.Column(db.String(100))
    property_taxes = db.Column(db.String(100))
    taxes_exempt = db.Column(db.String(100))

    def get_property_address(self):
        # lol didn't even think for the geocoding that in the denver database its assumed
        # that we're talking about addresses in denver Co so it isnt in the data
        # and so when geocoding i need to explicitly append Denver CO to the address I'm searching for.
        # this may clear up the 365 addresses that the site was unable to geocode
        return " ".join([self.site_number, self.site_dir, self.site_name, self.site_st_type, "Denver, CO"])

    def get_owner_address(self):
        return " ".join([self.owner_num,
                         self.owner_dir,
                         self.owner_st,
                         self.owner_st_type,
                         self.owner_city,
                         self.owner_state,
                         self.owner_zip]
                        )

    def to_dict(self):
        return {"id": self.id,
                "OWNER": self.owner,
                "CO_OWNER": self.co_owner,
                "OWNER_NUM": self.owner_num,
                "OWNER_DIR": self.owner_dir,
                "OWNER_ST": self.owner_st,
                "OWNER_TYPE": self.owner_st_type,
                "OWNER_APT": self.owner_apt,
                "OWNER_CITY": self.owner_city,
                "OWNER_STATE": self.owner_state,
                "OWNER_ZIP": self.owner_zip,
                "SITE_NBR": self.site_number,
                "SITE_DIR": self.site_dir,
                "SITE_NAME": self.site_name,
                "SITE_MODE": self.site_st_type,
                "SITE_MORE": self.site_more,
                "site_long": self.site_long,
                "site_lat": self.site_lat,
                "TOTAL_VALUE": self.property_value,
                "ASMT_TAXABLE": self.property_taxes,
                "ASMT_EXEMPT_AMT": self.taxes_exempt
                }


@app.route("/landlord", methods=["POST", "GET"])
def landlord():
    form = LandlordForm()
    if form.validate_on_submit():
        addies_list = []
        owner_addy = None
        entered_address = " ".join([form.number.data,
                                    form.direction.data,
                                    form.street.data.upper(),
                                    form.st_type.data,
                                    "Denver, CO"
                                    ])
        all_addies = Address.query.all()
        for addy in all_addies:
            if addy.get_property_address() == entered_address:
                owner_addy = addy.get_owner_address()
                break
        if owner_addy is None:
            flash("No records for that address")
            return render_template("landlord.html", form=form)
        for address in all_addies:
            if owner_addy == address.get_owner_address():
                location = Point((float(address.site_long), float(address.site_lat)))
                feature = Feature(geometry=location, properties={"owner": address.owner,
                                                                 "property_address": address.get_property_address(),
                                                                 "tax_address": address.get_owner_address(),
                                                                 "property_taxes": address.property_taxes,
                                                                 "property_value": address.property_value,
                                                                 "more info": address.site_more
                                                                 })
                addies_list.append(feature)
        feature_collection = FeatureCollection(addies_list)
        return render_template("map.html", addresses=feature_collection)
    return render_template("landlord.html", form=form)



@app.route("/test")
def test_db():
    list_of_owned_addies = []
    address = Address.query.first()
    owner_addy = address.get_owner_address()
    addies = Address.query.all()
    for addy in addies:
        if owner_addy == addy.get_owner_address():
            list_of_owned_addies.append(addy)
    list_of_addy_dicts = query_to_list_of_dicts(list_of_owned_addies)
    return jsonify(owned_addies=list_of_addy_dicts)